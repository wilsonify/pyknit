package org.pyknit.android

import android.annotation.SuppressLint
import android.content.ActivityNotFoundException
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.util.Log
import android.webkit.ConsoleMessage
import android.webkit.DownloadListener
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.webkit.WebViewAssetLoader
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Thin Android shell around the existing pyKnit web application.
 *
 * The full app (HTML/CSS/JS + PyScript + Pyodide + Python) is bundled in the
 * APK under assets/dist/ and served through [WebViewAssetLoader] on a local
 * https:// origin, so ES modules, fetch() and WebAssembly behave exactly like
 * they do over HTTP. No Chaquopy, no Python rewrite, no network required.
 *
 * Kotlin owns only Android concerns: asset serving with correct MIME types,
 * back navigation, export downloads, external links and diagnostics.
 */
class MainActivity : ComponentActivity() {
    private lateinit var webView: WebView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val assetLoader =
            WebViewAssetLoader.Builder()
                .setDomain(ASSET_DOMAIN)
                .addPathHandler("/", DistPathHandler(this))
                .build()

        webView = WebView(this)
        setContentView(webView)

        with(webView.settings) {
            javaScriptEnabled = true
            // Planner -> simulator handoff uses sessionStorage.
            domStorageEnabled = true
            databaseEnabled = true
            mediaPlaybackRequiresUserGesture = false
            loadWithOverviewMode = true
            useWideViewPort = true
            builtInZoomControls = false
            // Assets arrive over the https:// origin above, never file://.
            allowFileAccess = false
            allowContentAccess = false
            cacheMode = WebSettings.LOAD_DEFAULT
        }

        webView.webViewClient =
            object : WebViewClient() {
                override fun shouldInterceptRequest(
                    view: WebView,
                    request: WebResourceRequest,
                ): WebResourceResponse? {
                    if (!isOurOrigin(request.url)) {
                        return super.shouldInterceptRequest(view, request)
                    }
                    val served = assetLoader.shouldInterceptRequest(request.url)
                    if (served != null) {
                        return served
                    }
                    Log.w(TAG, "ASSET-MISS url=${request.url}")
                    return notFound()
                }

                @Suppress("DEPRECATION")
                override fun shouldInterceptRequest(
                    view: WebView,
                    url: String,
                ): WebResourceResponse? {
                    val uri = Uri.parse(url)
                    if (!isOurOrigin(uri)) {
                        return super.shouldInterceptRequest(view, url)
                    }
                    return assetLoader.shouldInterceptRequest(uri) ?: notFound()
                }

                override fun shouldOverrideUrlLoading(
                    view: WebView,
                    request: WebResourceRequest,
                ): Boolean {
                    return handleNavigation(request.url)
                }

                @Suppress("DEPRECATION")
                override fun shouldOverrideUrlLoading(
                    view: WebView,
                    url: String,
                ): Boolean {
                    return handleNavigation(Uri.parse(url))
                }

                override fun onReceivedHttpError(
                    view: WebView?,
                    request: WebResourceRequest?,
                    errorResponse: WebResourceResponse?,
                ) {
                    Log.e(
                        TAG,
                        "HTTP-ERROR url=${request?.url} " +
                            "code=${errorResponse?.statusCode} mime=${errorResponse?.mimeType}",
                    )
                    super.onReceivedHttpError(view, request, errorResponse)
                }

                override fun onReceivedError(
                    view: WebView?,
                    request: WebResourceRequest?,
                    error: android.webkit.WebResourceError?,
                ) {
                    Log.e(TAG, "LOAD-ERROR url=${request?.url} err=${error?.description}")
                    super.onReceivedError(view, request, error)
                }

                override fun onPageFinished(
                    view: WebView,
                    url: String,
                ) {
                    super.onPageFinished(view, url)
                    if (Uri.parse(url)?.host == ASSET_DOMAIN) {
                        view.evaluateJavascript(EXPORT_SHIM, null)
                    }
                }
            }

        webView.webChromeClient =
            object : WebChromeClient() {
                override fun onConsoleMessage(msg: ConsoleMessage): Boolean {
                    val line =
                        "CONSOLE[${msg.messageLevel()}] ${msg.message()} " +
                            "@ ${msg.sourceId()}:${msg.lineNumber()}"
                    if (msg.messageLevel() == ConsoleMessage.MessageLevel.ERROR) {
                        Log.e(TAG, line)
                    } else {
                        Log.i(TAG, line)
                    }
                    return super.onConsoleMessage(msg)
                }
            }

        webView.addJavascriptInterface(DiagnosticsBridge(), JAVASCRIPT_LOG)
        webView.addJavascriptInterface(ExportBridge(), JAVASCRIPT_EXPORT)

        webView.setDownloadListener(
            DownloadListener { url, _, _, _, _ ->
                handleDownload(url, suggestedName = null)
            },
        )

        onBackPressedDispatcher.addCallback(
            this,
            object : androidx.activity.OnBackPressedCallback(true) {
                override fun handleOnBackPressed() {
                    if (::webView.isInitialized && webView.canGoBack()) {
                        webView.goBack()
                    } else {
                        isEnabled = false
                        onBackPressedDispatcher.onBackPressed()
                    }
                }
            },
        )

        val startUrl = intent.getStringExtra(EXTRA_START_URL) ?: (ORIGIN + START_PAGE)
        Log.i(TAG, "Loading $startUrl")
        webView.loadUrl(startUrl)
    }

    override fun onDestroy() {
        if (::webView.isInitialized) {
            webView.destroy()
        }
        super.onDestroy()
    }

    private fun isOurOrigin(uri: Uri?): Boolean = uri?.host == ASSET_DOMAIN

    /** Returns true when the URL was consumed (external link opened). */
    private fun handleNavigation(uri: Uri?): Boolean {
        if (uri == null || isOurOrigin(uri)) {
            return false
        }
        if (uri.scheme == "http" || uri.scheme == "https") {
            try {
                startActivity(Intent(Intent.ACTION_VIEW, uri))
            } catch (e: ActivityNotFoundException) {
                Log.w(TAG, "No browser for $uri", e)
                toast("No app available to open this link")
            }
        } else {
            Log.w(TAG, "Ignoring non-http(s) navigation: $uri")
        }
        return true
    }

    private fun notFound(): WebResourceResponse = WebResourceResponse("text/plain", "utf-8", 404, "Not Found", emptyMap(), null)

    // ------------------------------------------------------------------
    // Exports (pattern .txt downloads produced by the demos)
    // ------------------------------------------------------------------

    private fun handleDownload(
        url: String,
        suggestedName: String?,
    ) {
        if (url.startsWith("data:text/plain")) {
            val payload = url.substringAfter(",", "")
            val text = decodeDataText(payload)
            saveExport(suggestedName ?: timestampedName(), text)
        } else {
            Log.w(TAG, "Unsupported download (only data:text/plain exports): $url")
            toast("This download type is not supported offline")
        }
    }

    private fun saveExport(
        fileName: String,
        text: String,
    ) {
        val safeName = sanitizeFileName(fileName)
        val bytes = text.toByteArray(Charsets.UTF_8)
        val location = writeTextFile(safeName, bytes)
        if (location != null) {
            Log.i(TAG, "Exported $safeName to $location")
            toast("Exported $safeName")
        } else {
            Log.e(TAG, "Export failed for $safeName")
            toast("Export failed")
        }
    }

    private fun writeTextFile(
        fileName: String,
        bytes: ByteArray,
    ): String? {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val values =
                    ContentValues().apply {
                        put(MediaStore.MediaColumns.DISPLAY_NAME, fileName)
                        put(MediaStore.MediaColumns.MIME_TYPE, "text/plain")
                        put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOCUMENTS)
                    }
                val uri =
                    contentResolver.insert(MediaStore.Files.getContentUri("external"), values)
                        ?: return null
                contentResolver.openOutputStream(uri)?.use { it.write(bytes) }
                uri.toString()
            } else {
                @Suppress("DEPRECATION")
                val dir =
                    getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS)
                        ?: filesDir
                if (!dir.isDirectory && !dir.mkdirs()) {
                    return null
                }
                val file = File(dir, fileName)
                file.writeBytes(bytes)
                file.absolutePath
            }
        } catch (e: Exception) {
            Log.e(TAG, "writeTextFile failed", e)
            null
        }
    }

    private fun toast(message: String) {
        runOnUiThread { Toast.makeText(this, message, Toast.LENGTH_LONG).show() }
    }

    private inner class DiagnosticsBridge {
        @JavascriptInterface
        fun log(message: String) {
            Log.i(TAG, "PAGE $message")
        }
    }

    private inner class ExportBridge {
        /** Called by the injected shim with the exact demo filename. */
        @JavascriptInterface
        fun save(
            fileName: String,
            dataUrl: String,
        ) {
            handleDownload(dataUrl, fileName.ifBlank { null })
        }
    }

    companion object {
        const val TAG = "PyknitWebView"
        const val ASSET_DOMAIN = "appassets.androidplatform.net"
        const val ORIGIN = "https://appassets.androidplatform.net"
        const val START_PAGE = "/index.html"
        const val EXTRA_START_URL = "start_url"
        private const val JAVASCRIPT_LOG = "__pyknitLog"
        private const val JAVASCRIPT_EXPORT = "__pyknitExport"

        /**
         * Click shim installed on every local page. Forwards the exact
         * `<a download>` filename + data URL to native code and suppresses
         * the stock download path (whose DownloadListener never sees the
         * filename). Only activates when the native bridge exists.
         */
        private const val EXPORT_SHIM =
            "(function(){if(!window.__pyknitExport||window.__pyknitExportShim)return;" +
                "window.__pyknitExportShim=true;" +
                "document.addEventListener('click',function(e){" +
                "var t=e.target&&e.target.closest?e.target.closest('a[download]'):null;" +
                "if(!t||!t.href||t.href.indexOf('data:text/plain')!==0)return;" +
                "e.preventDefault();e.stopPropagation();" +
                "window.__pyknitExport.save(t.download||'pyknit-export.txt',t.href);" +
                "},true);})();"

        fun sanitizeFileName(name: String): String {
            val safe = name.replace(Regex("[^A-Za-z0-9._-]"), "_").take(100).trim('_', '.', ' ')
            return safe.ifEmpty { "pyknit-export.txt" }
        }

        fun timestampedName(): String {
            val stamp = SimpleDateFormat("yyyyMMdd-HHmmss", Locale.US).format(Date())
            return "pyknit-export-$stamp.txt"
        }

        /**
         * Reverse of shared._download_text_file encoding (%, newline,
         * carriage return, space — in that order), so %25 decodes last.
         */
        fun decodeDataText(payload: String): String =
            payload
                .replace("%20", " ")
                .replace("%0D", "\r")
                .replace("%0A", "\n")
                .replace("%25", "%")
    }
}

/**
 * Serves assets/dist/ from the site root of the local https:// origin with
 * explicit MIME types (mirrors demos/nginx.conf, including
 * application/wasm and application/octet-stream for wheels).
 */
private class DistPathHandler(context: Context) : WebViewAssetLoader.PathHandler {
    private val assets = context.assets

    override fun handle(path: String): WebResourceResponse? {
        val clean = path.trimStart('/').split('/').filter { it.isNotEmpty() }
        if (clean.isEmpty() || ".." in clean) {
            return null
        }
        val assetPath = "dist/" + clean.joinToString("/")
        val mime = mimeFor(assetPath.substringAfterLast('.', ""))
        return try {
            val stream = assets.open(assetPath)
            val encoding = if (mime.startsWith("text/") || mime == "application/json") "utf-8" else null
            WebResourceResponse(mime, encoding, stream)
        } catch (e: Exception) {
            Log.w(MainActivity.TAG, "ASSET-MISS dist path=$assetPath")
            null
        }
    }

    private fun mimeFor(extension: String): String =
        when (extension.lowercase(Locale.US)) {
            "html" -> "text/html"
            "css" -> "text/css"
            "js", "mjs" -> "text/javascript"
            "json", "map" -> "application/json"
            "wasm" -> "application/wasm"
            "zip", "whl" -> "application/octet-stream"
            "png" -> "image/png"
            "svg" -> "image/svg+xml"
            "ico" -> "image/x-icon"
            "txt", "py" -> "text/plain"
            else -> "application/octet-stream"
        }
}
