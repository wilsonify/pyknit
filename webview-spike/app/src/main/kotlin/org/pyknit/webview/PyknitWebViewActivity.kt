package org.pyknit.webview

import android.annotation.SuppressLint
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.webkit.ConsoleMessage
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.webkit.WebViewAssetLoader

/**
 * Minimal WebView shell for the pyKnit spike. No Chaquopy, no Python rewrite.
 *
 * - Serves bundled web assets via WebViewAssetLoader at
 *   https://appassets.androidplatform.net/dist/... (same-origin so that
 *   ES modules, fetch(), and Pyodide's WASM loader behave like HTTP).
 * - Enables exactly what Pyodide/PyScript need: JavaScript, DOM storage
 *   (sessionStorage drives planner->simulator handoff), media playback
 *   not required.
 * - Captures console errors, JS exceptions, and failed resource loads to
 *   logcat tag [PyknitWebView] so failures can be classified A..G.
 * - Exposes window.__pyknitBridge = { ready:false } which the smoke page
 *   flips to {ready:true} once loadPyodide() resolves.
 */
class PyknitWebViewActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var assetLoader: WebViewAssetLoader

    companion object {
        const val TAG = "PyknitWebView"
        const val ORIGIN = "https://appassets.androidplatform.net"
        /** Change to "/dist/index.html" to boot the real landing page. */
        const val START_PAGE = "/dist/smoke/pyodide-smoke.html"
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        assetLoader = WebViewAssetLoader.Builder()
            .setDomain("appassets.androidplatform.net")
            .addPathHandler("/dist/", WebViewAssetLoader.AssetsPathHandler(this, "dist"))
            .build()

        webView = WebView(this)
        setContentView(webView)

        with(webView.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true // sessionStorage/localStorage for planner handoff
            databaseEnabled = true
            mediaPlaybackRequiresUserGesture = false
            loadWithOverviewMode = true
            useWideViewPort = true
            builtInZoomControls = false
            // Keep file:// access OFF on purpose: assets come via the
            // https:// origin above, never via file:// URLs.
            allowFileAccess = false
            allowContentAccess = false
            cacheMode = WebSettings.LOAD_DEFAULT
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest,
            ): WebResourceResponse? {
                val url = request.url.toString()
                if (url.startsWith(ORIGIN)) {
                    val intercepted = assetLoader.shouldInterceptRequest(request.url)
                    if (intercepted != null) return intercepted
                    Log.w(TAG, "ASSET-MISS url=$url (packaging bug if this is a .wasm/.whl/.mjs)")
                }
                return super.shouldInterceptRequest(view, request)
            }

            override fun onReceivedHttpError(
                view: WebView?,
                request: WebResourceRequest?,
                errorResponse: WebResourceResponse?,
            ) {
                Log.e(
                    TAG,
                    "HTTP-ERROR url=${request?.url} code=${errorResponse?.statusCode} " +
                        "mime=${errorResponse?.mimeType}",
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
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onConsoleMessage(msg: ConsoleMessage): Boolean {
                val level = msg.messageLevel().name
                Log.i(TAG, "CONSOLE[$level] ${msg.message()} @ ${msg.sourceId()}:${msg.lineNumber()}")
                if (level == "ERROR") {
                    Log.e(TAG, "JS-CONSOLE-ERROR ${msg.message()}")
                }
                return super.onConsoleMessage(msg)
            }
        }

        // Optional JS bridge: pages can call window.__pyknitLog("pyodide-ready")
        webView.addJavascriptInterface(
            object {
                @android.webkit.JavascriptInterface
                fun log(message: String) {
                    Log.i(TAG, "PAGE-BRIDGE $message")
                }
            },
            "__pyknitLog",
        )

        val startUrl = intent.getStringExtra("start_url") ?: (ORIGIN + START_PAGE)
        Log.i(TAG, "Loading $startUrl")
        webView.loadUrl(startUrl)
    }

    override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) webView.goBack()
        else super.onBackPressed()
    }

    override fun onDestroy() {
        if (::webView.isInitialized) webView.destroy()
        super.onDestroy()
    }
}
