package org.pyknit.android.ui

import android.animation.ValueAnimator
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapShader
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Path
import android.graphics.PathMeasure
import android.graphics.RectF
import android.graphics.Shader
import android.view.View
import android.view.animation.DecelerateInterpolator
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min

/**
 * Port of the pyscript demo's garment renderer to a native Canvas view.
 *
 * Modes mirror the web demo exactly: small manual patterns become a swatch
 * with live stitches on a needle; manual sweaters and hat plans grow as a
 * bottom-up sweater; raglan plans construct top-down with separate sleeves;
 * sock plans follow the calculator's centerline. The reveal animates with a
 * short ease-out, matching the demo.
 */
class GarmentView(context: Context) : View(context) {
    private enum class Mode { NONE, SWATCH, SWEATER, RAGLAN, SOCK }

    private var mode = Mode.NONE
    private var steps: JSONArray = JSONArray()
    private var index = 0
    private var sim: JSONObject? = null
    private var reveal = 0f

    // Raglan reveal is a (torso, left sleeve, right sleeve) triple, each a
    // length in viewBox units revealed from the top of its piece.
    private var raglanT = 0f
    private var raglanSL = 0f
    private var raglanSR = 0f
    private var animator: ValueAnimator? = null

    // ---- sweater / raglan geometry (viewBox 320x340) ----
    private val topY = 64f
    private val hemY = 318f
    private val minReveal = 12f
    private val minSliver = 12f
    private val sleeveLen = 252f
    private val sleeveTopY = 66f
    private val underarmY = 152f

    // ---- swatch geometry ----
    private val swX0 = 40f
    private val swX1 = 280f
    private val fabricY = 82f
    private var swatchRowH = 30f

    init {
        // clipPath + blur need a software canvas; the view is small and only
        // redraws on step changes, so this is cheap.
        setLayerType(View.LAYER_TYPE_SOFTWARE, null)
    }

    fun setSimulation(
        sim: JSONObject?,
        steps: JSONArray,
        index: Int,
        animate: Boolean = true,
    ) {
        this.sim = sim
        this.steps = steps
        this.index = index.coerceIn(0, (steps.length() - 1).coerceAtLeast(0))
        val newMode = modeFor(sim, steps)
        val target = revealFor(newMode, this.index)
        val rgTarget = if (newMode == Mode.RAGLAN) raglanReveals() else null
        if (newMode != mode) {
            reveal = target
            raglanT = rgTarget?.first ?: 0f
            raglanSL = rgTarget?.second ?: 0f
            raglanSR = rgTarget?.third ?: 0f
        }
        mode = newMode
        animator?.cancel()
        val animated = animate && mode != Mode.NONE
        if (animated && rgTarget != null && (raglanT != rgTarget.first || raglanSL != rgTarget.second || raglanSR != rgTarget.third)) {
            val t0 = raglanT
            val sl0 = raglanSL
            val sr0 = raglanSR
            animator =
                ValueAnimator.ofFloat(0f, 1f).apply {
                    duration = 220
                    interpolator = DecelerateInterpolator()
                    addUpdateListener {
                        val k = it.animatedValue as Float
                        raglanT = t0 + (rgTarget.first - t0) * k
                        raglanSL = sl0 + (rgTarget.second - sl0) * k
                        raglanSR = sr0 + (rgTarget.third - sr0) * k
                        invalidate()
                    }
                    start()
                }
        } else if (animated && rgTarget == null && target != reveal) {
            animator =
                ValueAnimator.ofFloat(reveal, target).apply {
                    duration = 220
                    interpolator = DecelerateInterpolator()
                    addUpdateListener {
                        reveal = it.animatedValue as Float
                        invalidate()
                    }
                    start()
                }
        } else {
            reveal = target
            if (rgTarget != null) {
                raglanT = rgTarget.first
                raglanSL = rgTarget.second
                raglanSR = rgTarget.third
            }
        }
        invalidate()
    }

    private fun modeFor(
        sim: JSONObject?,
        steps: JSONArray,
    ): Mode {
        val garment = sim?.optString("garment") ?: "sweater"
        return when (garment) {
            "sock" -> Mode.SOCK
            "raglan" -> Mode.RAGLAN
            "sweater" -> {
                val castOn = steps.optJSONObject(0)?.optInt("n", 0) ?: 0
                val rows = steps.length() - 1
                if (castOn in 1..24 && rows in 1..60) Mode.SWATCH else Mode.SWEATER
            }
            else -> Mode.SWEATER
        }
    }

    private fun revealFor(
        mode: Mode,
        i: Int,
    ): Float =
        when (mode) {
            Mode.NONE -> 0f
            Mode.SWATCH -> i.toFloat()
            Mode.SOCK -> {
                val total = (steps.length() - 1).coerceAtLeast(1)
                val f = i.toFloat() / total
                18f + f * (sockTotalLen() - 18f)
            }
            Mode.RAGLAN -> i.toFloat() // interpreted piece-by-piece in drawRaglan
            Mode.SWEATER -> {
                val totalRows = (steps.length() - 1).coerceAtLeast(1)
                val bandH = (hemY - topY) / totalRows
                (340f - hemY) + minReveal + i * bandH
            }
        }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        when (mode) {
            Mode.NONE -> drawPlaceholder(canvas)
            Mode.SWATCH -> drawSwatch(canvas)
            Mode.SWEATER -> drawSweater(canvas)
            Mode.RAGLAN -> drawRaglan(canvas)
            Mode.SOCK -> drawSock(canvas)
        }
    }

    // ------------------------------------------------------------------
    // shared drawing helpers
    // ------------------------------------------------------------------

    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)

    private fun Canvas.fit(
        vw: Float,
        vh: Float,
    ) {
        val sx = width / vw
        val sy = height / vh
        val s = min(sx, sy)
        val dx = (width - vw * s) / 2f
        val dy = (height - vh * s) / 2f
        save()
        translate(dx, dy)
        scale(s, s)
    }

    private fun color(
        hex: Long,
        alpha: Int = 255,
    ): Int = Color.argb(alpha, ((hex shr 16) and 0xFF).toInt(), ((hex shr 8) and 0xFF).toInt(), (hex and 0xFF).toInt())

    private fun accent(alpha: Int): Int = color(0x5A2A75, alpha)

    private fun shade(alpha: Int): Int = color(0x2B2333, alpha)

    private fun knitPattern(
        color: Int,
        vw: Float = 12f,
        vh: Float = 8f,
    ): BitmapShader {
        val bmp = Bitmap.createBitmap(vw.toInt(), vh.toInt(), Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        val p =
            Paint(Paint.ANTI_ALIAS_FLAG).apply {
                this.color = color
                style = Paint.Style.STROKE
                strokeWidth = 1.1f
                strokeCap = Paint.Cap.ROUND
                strokeJoin = Paint.Join.ROUND
            }
        val path =
            Path().apply {
                moveTo(3f, vh - 0.8f)
                lineTo(vw / 2f, 1.8f)
                lineTo(vw - 3f, vh - 0.8f)
            }
        c.drawPath(path, p)
        return BitmapShader(bmp, Shader.TileMode.REPEAT, Shader.TileMode.REPEAT)
    }

    private fun ribPattern(color: Int): BitmapShader {
        val bmp = Bitmap.createBitmap(7, 7, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        val p =
            Paint(Paint.ANTI_ALIAS_FLAG).apply {
                this.color = color
                style = Paint.Style.STROKE
                strokeWidth = 1f
            }
        c.drawLine(1.8f, 0f, 1.8f, 7f, p)
        c.drawLine(5.2f, 0f, 5.2f, 7f, p)
        return BitmapShader(bmp, Shader.TileMode.REPEAT, Shader.TileMode.REPEAT)
    }

    private fun gradient(
        colors: IntArray,
        horizontal: Boolean = true,
    ): LinearGradient =
        if (horizontal) {
            LinearGradient(0f, 0f, 320f, 0f, colors, null, Shader.TileMode.CLAMP)
        } else {
            LinearGradient(0f, 0f, 0f, 230f, colors, null, Shader.TileMode.CLAMP)
        }

    private val fabricColors =
        intArrayOf(
            color(0xC4A8D8),
            color(0xE8DBF1),
            color(0xC4A8D8),
        )
    private val sockColors =
        intArrayOf(
            color(0xEEF0FA),
            color(0xDBE0F3),
            color(0xC2CBE9),
        )

    private val knitPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { shader = knitPattern(accent(40)) }
    private val ribPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { shader = ribPattern(accent(36)) }
    private val ribTint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.argb(26, 123, 63, 160) }
    private val shadePaint =
        Paint(Paint.ANTI_ALIAS_FLAG).apply {
            shader =
                LinearGradient(
                    0f,
                    0f,
                    320f,
                    0f,
                    intArrayOf(shade(51), Color.TRANSPARENT, Color.TRANSPARENT, shade(51)),
                    null,
                    Shader.TileMode.CLAMP,
                )
        }

    private fun isRib(step: JSONObject): Boolean {
        val ops = step.optJSONArray("row_ops") ?: return false
        for (i in 0 until ops.length()) if (ops.optInt(i) == 1) return true
        return false
    }

    private fun drawPlaceholder(canvas: Canvas) {
        paint.color = color(0x8A7A97)
        paint.textSize = 14f * resources.displayMetrics.density
        paint.textAlign = Paint.Align.CENTER
        paint.typeface = android.graphics.Typeface.DEFAULT
        canvas.drawText("Build the simulation to see the knitting.", width / 2f, height / 2f, paint)
    }

    // ------------------------------------------------------------------
    // sweater (bottom-up; used for manual sweaters and hat plans)
    // ------------------------------------------------------------------

    private fun sweaterSilhouette(): Path =
        Path().apply {
            moveTo(56f, hemY)
            lineTo(66f, 150f)
            lineTo(100f, topY)
            lineTo(108f, topY)
            cubicTo(130f, 108f, 190f, 108f, 212f, topY)
            lineTo(220f, topY)
            lineTo(254f, 150f)
            lineTo(264f, hemY)
            close()
        }

    private fun drawSweater(canvas: Canvas) {
        val totalRows = (steps.length() - 1).coerceAtLeast(1)
        val bandH = (hemY - topY) / totalRows
        val revealH = reveal.coerceIn(minReveal, 340f - topY + minReveal)
        val clipTop = 340f - revealH

        canvas.save()
        canvas.fit(320f, 340f)
        drawShadow(canvas, 118f)

        // fabric, clipped to the revealed region
        canvas.save()
        canvas.clipRect(0f, clipTop, 320f, 340f)
        canvas.drawRect(0f, 0f, 320f, 340f, Paint(Paint.ANTI_ALIAS_FLAG).apply { shader = gradient(fabricColors) })
        canvas.drawRect(0f, 0f, 320f, 340f, knitPaint)
        // side shading
        canvas.drawRect(0f, 0f, 320f, 340f, shadePaint)
        // rib bands
        for (i in 1 until steps.length()) {
            if (isRib(steps.getJSONObject(i))) {
                val top = hemY - i * bandH
                canvas.drawRect(0f, top - bandH, 320f, top, ribTint)
            }
        }
        // separators between bands
        val sep =
            Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = shade(31)
                strokeWidth = 1f
            }
        for (i in 1 until steps.length() - 1) {
            val y = hemY - i * bandH
            canvas.drawLine(0f, y, 320f, y, sep)
        }
        // neckline + hem
        val neck =
            Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = color(0xB39BCB)
                strokeWidth = 11f
                style = Paint.Style.STROKE
                strokeCap = Paint.Cap.ROUND
            }
        val neckPath =
            Path().apply {
                moveTo(108f, topY)
                cubicTo(130f, 108f, 190f, 108f, 212f, topY)
            }
        canvas.drawPath(neckPath, neck)
        drawHemStrip(canvas, hemY - minReveal)
        canvas.restore()

        // outline on top of the reveal
        canvas.save()
        canvas.clipRect(0f, clipTop, 320f, 340f)
        val outline =
            Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = accent(72)
                strokeWidth = 2f
                style = Paint.Style.STROKE
                strokeJoin = Paint.Join.ROUND
            }
        canvas.drawPath(sweaterSilhouette(), outline)
        canvas.restore()

        canvas.restore()
    }

    private fun drawShadow(
        canvas: Canvas,
        rx: Float,
    ) {
        val shadow =
            Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = shade(26)
                maskFilter = android.graphics.BlurMaskFilter(5f, android.graphics.BlurMaskFilter.Blur.NORMAL)
            }
        canvas.drawOval(RectF(160f - rx, 325f, 160f + rx, 333f), shadow)
    }

    private fun drawHemStrip(
        canvas: Canvas,
        y: Float,
    ) {
        canvas.drawRect(0f, y, 320f, y + minReveal, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = accent(46) })
        canvas.drawRect(0f, y, 320f, y + minReveal, ribPaint)
    }

    // ------------------------------------------------------------------
    // raglan (top-down: torso + two sleeves)
    // ------------------------------------------------------------------

    private fun raglanTorsoPath(flare: Float): Path =
        Path().apply {
            val sx = 108f - 16f * flare
            val ex = 212f + 16f * flare
            moveTo(108f, topY)
            cubicTo(130f, 108f, 190f, 108f, 212f, topY)
            lineTo(ex, underarmY)
            lineTo(ex, hemY)
            lineTo(sx, hemY)
            lineTo(sx, underarmY)
            close()
        }

    private fun sleevePath(left: Boolean): Path =
        Path().apply {
            if (left) {
                moveTo(74f, 76f)
                lineTo(108f, 66f)
                lineTo(92f, underarmY)
                lineTo(92f, hemY - 12f)
                quadTo(92f, hemY, 86f, hemY)
                lineTo(68f, hemY)
                quadTo(62f, hemY, 62f, hemY - 12f)
                lineTo(62f, 84f)
            } else {
                moveTo(246f, 76f)
                lineTo(212f, 66f)
                lineTo(228f, underarmY)
                lineTo(228f, hemY - 12f)
                quadTo(228f, hemY, 234f, hemY)
                lineTo(252f, hemY)
                quadTo(258f, hemY, 258f, hemY - 12f)
                lineTo(258f, 84f)
            }
            close()
        }

    private fun raglanSections(): RaglanSections {
        val sections = sim?.optJSONArray("sections")
        var bodyEnd = -1
        var s1Start = -1
        var s1End = -1
        var s2Start = -1
        var s2End = -1
        var lastOtherEnd = 0
        if (sections != null) {
            for (i in 0 until sections.length()) {
                val sec = sections.getJSONObject(i)
                val id = sec.optString("id")
                val start = sec.optInt("start")
                val end = sec.optInt("end")
                when (id) {
                    "left_sleeve" -> {
                        s1Start = start
                        s1End = end
                    }
                    "right_sleeve" -> {
                        s2Start = start
                        s2End = end
                    }
                    "body" -> bodyEnd = end
                    else -> lastOtherEnd = max(lastOtherEnd, end)
                }
            }
        }
        val total = steps.length()
        if (bodyEnd < 0) {
            bodyEnd =
                if (sections == null || sections.length() == 0) {
                    (total * 0.6f).toInt().coerceAtLeast(1)
                } else {
                    lastOtherEnd.coerceAtLeast(1)
                }
        }
        if (s1Start < 0) {
            s1Start = bodyEnd
            s1End = bodyEnd + (total - bodyEnd) / 3
        }
        if (s2Start < 0) {
            s2Start = s1End
            s2End = total
        }
        return RaglanSections(bodyEnd, s1Start, s1End, s2Start, s2End)
    }

    private data class RaglanSections(
        val bodyEnd: Int,
        val s1Start: Int,
        val s1End: Int,
        val s2Start: Int,
        val s2End: Int,
    )

    private fun raglanFlare(): Float {
        val sections = sim?.optJSONArray("sections") ?: return 1f
        for (i in 0 until sections.length()) {
            val sec = sections.getJSONObject(i)
            if (sec.optString("id") == "yoke") {
                val start = sec.optInt("start")
                val len = (sec.optInt("end") - start).coerceAtLeast(1)
                if (index < start) return 0f
                if (index >= start + len) return 1f
                return ((index - start + 1).toFloat() / len).coerceIn(0f, 1f)
            }
        }
        return 1f
    }

    /** Raglan reveal lengths (torso, left sleeve, right sleeve), mirroring the
     * web demo: the torso reaches the hem exactly when the body section ends,
     * and each sleeve reveals through its own section. */
    private fun raglanReveals(): Triple<Float, Float, Float> {
        val s = raglanSections()
        val torsoFull = hemY - topY
        val torso =
            if (index < s.bodyEnd) {
                minSliver + (index + 1f) / s.bodyEnd * (torsoFull - minSliver)
            } else {
                torsoFull
            }

        fun sleeve(
            start: Int,
            end: Int,
        ): Float {
            if (index < start) return 0f
            val f = (index - start + 1f) / (end - start).coerceAtLeast(1)
            return minSliver + min(1f, f) * (sleeveLen - minSliver)
        }
        return Triple(torso, sleeve(s.s1Start, s.s1End), sleeve(s.s2Start, s.s2End))
    }

    private fun drawRaglan(canvas: Canvas) {
        val torsoReveal = (topY + raglanT).coerceIn(topY, hemY + 2f)
        val sleeveLReveal = (sleeveTopY + raglanSL).coerceIn(0f, hemY + 2f)
        val sleeveRReveal = (sleeveTopY + raglanSR).coerceIn(0f, hemY + 2f)
        val flare = raglanFlare()

        canvas.save()
        canvas.fit(320f, 340f)
        drawShadow(canvas, 118f)

        val torso = raglanTorsoPath(flare)
        drawPiece(canvas, torso, RectF(0f, topY, 320f, torsoReveal), topDown = true) { c ->
            // wedge + seams + hem
            val wedge =
                Path().apply {
                    moveTo(108f, topY)
                    lineTo(212f, topY)
                    lineTo(212f + 16f * flare, underarmY)
                    lineTo(108f - 16f * flare, underarmY)
                    close()
                }
            val wedgePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.argb(31, 123, 63, 160) }
            c.drawPath(wedge, wedgePaint)
            val seam =
                Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    color = accent(102)
                    strokeWidth = 2.5f
                    style = Paint.Style.STROKE
                    strokeCap = Paint.Cap.ROUND
                }
            c.drawLine(108f, topY, 108f - 16f * flare, underarmY, seam)
            c.drawLine(212f, topY, 212f + 16f * flare, underarmY, seam)
            drawHemStrip(c, hemY - minReveal)
        }
        drawPieceOutline(canvas, torso, RectF(0f, topY, 320f, torsoReveal), topDown = true) { c ->
            val outline =
                Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    color = accent(82)
                    strokeWidth = 2f
                    style = Paint.Style.STROKE
                    strokeJoin = Paint.Join.ROUND
                }
            c.drawPath(torso, outline)
            val neck =
                Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    color = Color.argb(140, 123, 63, 160)
                    strokeWidth = 6f
                    style = Paint.Style.STROKE
                    strokeCap = Paint.Cap.ROUND
                }
            val neckPath =
                Path().apply {
                    moveTo(108f, topY)
                    cubicTo(130f, 108f, 190f, 108f, 212f, topY)
                }
            c.drawPath(neckPath, neck)
        }

        val sleeveL = sleevePath(left = true)
        val sleeveR = sleevePath(left = false)
        drawPiece(canvas, sleeveL, RectF(0f, sleeveTopY, 320f, sleeveLReveal), topDown = true) { c ->
            drawHemStrip(c, hemY - minReveal)
        }
        drawPieceOutline(canvas, sleeveL, RectF(0f, sleeveTopY, 320f, sleeveLReveal), topDown = true) { c ->
            val outline =
                Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    color = accent(82)
                    strokeWidth = 2f
                    style = Paint.Style.STROKE
                    strokeJoin = Paint.Join.ROUND
                }
            c.drawPath(sleeveL, outline)
        }
        drawPiece(canvas, sleeveR, RectF(0f, sleeveTopY, 320f, sleeveRReveal), topDown = true) { c ->
            drawHemStrip(c, hemY - minReveal)
        }
        drawPieceOutline(canvas, sleeveR, RectF(0f, sleeveTopY, 320f, sleeveRReveal), topDown = true) { c ->
            val outline =
                Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    color = accent(82)
                    strokeWidth = 2f
                    style = Paint.Style.STROKE
                    strokeJoin = Paint.Join.ROUND
                }
            c.drawPath(sleeveR, outline)
        }

        canvas.restore()
    }

    /** Draws fabric (gradient + knit + shade) inside a piece clip + reveal clip. */
    private inline fun drawPiece(
        canvas: Canvas,
        piece: Path,
        revealRect: RectF,
        topDown: Boolean,
        extras: (Canvas) -> Unit,
    ) {
        canvas.save()
        canvas.clipPath(piece)
        canvas.clipRect(revealRect)
        canvas.drawRect(0f, 0f, 320f, 340f, Paint(Paint.ANTI_ALIAS_FLAG).apply { shader = gradient(fabricColors) })
        canvas.drawRect(0f, 0f, 320f, 340f, knitPaint)
        canvas.drawRect(0f, 0f, 320f, 340f, shadePaint)
        extras(canvas)
        canvas.restore()
    }

    private inline fun drawPieceOutline(
        canvas: Canvas,
        piece: Path,
        revealRect: RectF,
        topDown: Boolean,
        extras: (Canvas) -> Unit,
    ) {
        canvas.save()
        canvas.clipPath(piece)
        canvas.clipRect(revealRect)
        extras(canvas)
        canvas.restore()
    }

    // ------------------------------------------------------------------
    // sock (bent schematic revealed along the knitting centerline)
    // ------------------------------------------------------------------

    private fun sockGeometry(): Pair<Float, Float> {
        val castOn = sim?.optJSONObject("sock_summary")?.optInt("cast_on_stitches") ?: steps.optJSONObject(0)?.optInt("n") ?: 64
        val ankle = sim?.optJSONObject("sock_summary")?.optInt("ankle_stitches") ?: castOn
        val cuffDepth = (16f + castOn * 0.5f).coerceIn(26f, 64f)
        val ankleDepth = (14f + ankle * 0.45f).coerceIn(24f, 58f)
        return cuffDepth to ankleDepth
    }

    private fun sockSilhouette(g: Pair<Float, Float>): Path =
        Path().apply {
            val (cuff, ankle) = g
            moveTo(26f, 26f)
            lineTo(26f, 192f)
            lineTo(204f, 192f)
            quadTo(268f, 192f, 268f, 160f)
            lineTo(26f + ankle, 152f)
            lineTo(26f + cuff, 26f)
            close()
        }

    private fun sockCenterline(g: Pair<Float, Float>): Path =
        Path().apply {
            val (cuff, ankle) = g
            moveTo(26f, 26f)
            lineTo(26f + cuff, 26f)
            lineTo(26f + ankle, 152f)
            lineTo(26f + ankle, 192f)
            lineTo(34f, 192f)
            lineTo(204f, 192f)
            quadTo(268f, 192f, 268f, 160f)
        }

    private fun sockTotalLen(): Float {
        val g = sockGeometry()
        return PathMeasure(sockCenterline(g), false).length
    }

    /** Converts a stroked path to a filled ribbon path (for the reveal mask). */
    private fun strokeToFill(
        path: Path,
        width: Float,
        step: Float = 2f,
    ): Path {
        val pm = PathMeasure(path, false)
        val len = pm.length
        val left = mutableListOf<FloatArray>()
        val right = mutableListOf<FloatArray>()
        val pts = FloatArray(2)
        val tan = FloatArray(2)
        var t = 0f
        while (t <= len) {
            pm.getPosTan(t, pts, tan)
            val n = hypot(tan[0], tan[1]).coerceAtLeast(0.0001f)
            val ox = -tan[1] / n * width / 2f
            val oy = tan[0] / n * width / 2f
            left.add(floatArrayOf(pts[0] + ox, pts[1] + oy))
            right.add(floatArrayOf(pts[0] - ox, pts[1] - oy))
            t += step
        }
        right.reverse()
        val mask = Path()
        (left + right).forEachIndexed { i, p ->
            if (i == 0) mask.moveTo(p[0], p[1]) else mask.lineTo(p[0], p[1])
        }
        mask.close()
        return mask
    }

    private fun drawSock(canvas: Canvas) {
        val g = sockGeometry()
        val silhouette = sockSilhouette(g)
        val center = sockCenterline(g)
        val totalLen = PathMeasure(center, false).length
        val revealLen = reveal.coerceIn(18f, totalLen)
        // trim the mask to the revealed length
        val revealedMask = strokeToFill(trimmedPath(center, revealLen), 112f)

        canvas.save()
        canvas.fit(360f, 230f)
        // shadow
        val shadow =
            Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = shade(26)
                maskFilter = android.graphics.BlurMaskFilter(5f, android.graphics.BlurMaskFilter.Blur.NORMAL)
            }
        canvas.drawOval(RectF(18f, 210f, 282f, 218f), shadow)

        // fabric clipped to silhouette + revealed mask
        canvas.save()
        canvas.clipPath(silhouette)
        canvas.clipPath(revealedMask)
        canvas.drawRect(
            0f,
            0f,
            360f,
            230f,
            Paint(Paint.ANTI_ALIAS_FLAG).apply {
                shader = LinearGradient(0f, 0f, 360f, 230f, sockColors, null, Shader.TileMode.CLAMP)
            },
        )
        canvas.drawRect(0f, 0f, 360f, 230f, Paint(Paint.ANTI_ALIAS_FLAG).apply { shader = knitPattern(accent(38), 11f, 8f) })
        // regions: rib cuff + heel
        val total = (steps.length() - 1).coerceAtLeast(1)
        var ribN = 0
        var heelN = 0
        val decPts = mutableListOf<Int>()
        for (i in 0 until steps.length()) {
            val st = steps.getJSONObject(i)
            val tex = st.optString("texture")
            if (tex == "rib") ribN++
            if (tex == "heel" || tex == "gusset") heelN++
            if (st.optInt("decreases") > 0) decPts.add(i)
        }
        val legLen = 192f - 26f
        val cuffH = (ribN.toFloat() / total * legLen).coerceIn(16f, 92f)
        val heelH = (heelN.toFloat() / total * legLen + 10f).coerceIn(14f, 70f)
        val (cuff, ankle) = g
        if (ribN > 0) {
            canvas.drawRect(24f, 24f, 26f + cuff + 2f, 24f + cuffH, ribTint)
            canvas.drawRect(24f, 24f, 26f + cuff + 2f, 24f + cuffH, ribPaint)
        }
        if (heelN > 0) {
            val heelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.argb(33, 123, 63, 160) }
            canvas.drawRect(24f, 192f - heelH, 26f + ankle + 2f, 192f, heelPaint)
        }
        canvas.restore()

        // outline
        canvas.save()
        canvas.clipPath(silhouette)
        canvas.clipPath(revealedMask)
        val outline =
            Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = accent(82)
                strokeWidth = 2f
                style = Paint.Style.STROKE
                strokeJoin = Paint.Join.ROUND
            }
        canvas.drawPath(silhouette, outline)
        canvas.restore()

        canvas.restore()
    }

    private fun trimmedPath(
        path: Path,
        length: Float,
        step: Float = 2f,
    ): Path {
        val pm = PathMeasure(path, false)
        val total = pm.length
        val out = Path()
        val pts = FloatArray(2)
        var t = 0f
        var first = true
        while (t <= length.coerceAtMost(total)) {
            pm.getPosTan(t, pts, null)
            if (first) {
                out.moveTo(pts[0], pts[1])
                first = false
            } else {
                out.lineTo(pts[0], pts[1])
            }
            t += step
        }
        return out
    }

    // ------------------------------------------------------------------
    // swatch (small manual patterns: live stitches + worked rows)
    // ------------------------------------------------------------------

    private fun swatchNeedleY(x: Float): Float = 52f + (x - 28f) * (60f - 52f) / 264f

    private fun swatchStitchPath(
        code: Int,
        cx: Float,
        y: Float,
        rowH: Float,
        spacing: Float,
    ): Path {
        val h = rowH * 0.74f
        val w = (spacing * 0.42f).coerceIn(2.2f, 5f)
        val top = y + rowH * 0.14f
        val p = Path()
        when (code) {
            1 -> { // purl bump
                val bw = w * 1.25f
                val by = top + h * 0.26f
                p.moveTo(cx - bw, by)
                p.quadTo(cx, by + h * 0.34f, cx + bw, by)
            }
            2 -> { // yarn over loop
                p.addOval(RectF(cx - max(2.2f, w * 0.6f), top + h * 0.08f, cx + max(2.2f, w * 0.6f), top + h * 0.92f), Path.Direction.CW)
            }
            3, 4 -> { // decrease / bind-off: V + merge mark handled by extra stroke
                p.moveTo(cx - w, top)
                p.lineTo(cx, top + h)
                p.lineTo(cx + w, top)
            }
            else -> { // knit V
                p.moveTo(cx - w, top)
                p.lineTo(cx, top + h)
                p.lineTo(cx + w, top)
            }
        }
        return p
    }

    private fun swatchStitchColor(code: Int): Int =
        when (code) {
            1 -> color(0x3F2459)
            2 -> color(0xB98CD9)
            3 -> color(0xA33E5C)
            4 -> color(0x8A6BB0)
            else -> color(0x7C55B0)
        }

    private fun drawSwatchRow(
        canvas: Canvas,
        rowIdx: Int,
        step: JSONObject,
        y: Float,
        rowH: Float,
    ) {
        val ops = step.optJSONArray("row_ops")
        val worked = ops?.length() ?: 1
        val w = (swX1 - swX0) / max(worked, 1)
        // row number
        paint.color = color(0xB3A6C2)
        paint.textSize = 9f
        paint.textAlign = Paint.Align.CENTER
        canvas.drawText((rowIdx + 1).toString(), 21f, y + rowH * 0.62f, paint)
        if (ops == null) return
        for (i in 0 until ops.length()) {
            val code = ops.optInt(i)
            val cx = swX0 + (i + 0.5f) * w
            val path = swatchStitchPath(code, cx, y, rowH, w)
            val stroke =
                Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    color = swatchStitchColor(code)
                    style = Paint.Style.STROKE
                    strokeWidth = 2.4f
                    strokeCap = Paint.Cap.ROUND
                    strokeJoin = Paint.Join.ROUND
                }
            canvas.drawPath(path, stroke)
            if (code == 3 || code == 4) { // merge mark above the V
                val top = y + rowH * 0.14f
                val h = rowH * 0.74f
                val merge =
                    Paint(Paint.ANTI_ALIAS_FLAG).apply {
                        color = swatchStitchColor(code)
                        style = Paint.Style.STROKE
                        strokeWidth = 1.7f
                        strokeCap = Paint.Cap.ROUND
                    }
                val mp =
                    Path().apply {
                        moveTo(cx - w * 1.7f, top + h * 0.16f)
                        quadTo(cx, top - 3f, cx + w * 1.7f, top + h * 0.16f)
                    }
                canvas.drawPath(mp, merge)
            }
        }
    }

    private fun drawSwatch(canvas: Canvas) {
        val totalRows = (steps.length() - 1).coerceAtLeast(1)
        swatchRowH = (320f / totalRows).coerceIn(8f, 30f)
        val fabH = totalRows * swatchRowH
        val vh = fabricY + fabH + 18f

        canvas.save()
        canvas.fit(320f, vh)

        // fabric panel
        val panel =
            Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = color(0xF7F2FC)
                style = Paint.Style.FILL
            }
        canvas.drawRoundRect(RectF(30f, fabricY - 6f, 290f, fabricY + fabH + 6f), 8f, 8f, panel)
        val panelStroke =
            Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = accent(31)
                style = Paint.Style.STROKE
                strokeWidth = 1f
            }
        canvas.drawRoundRect(RectF(30f, fabricY - 6f, 290f, fabricY + fabH + 6f), 8f, 8f, panelStroke)

        // needle
        val needle =
            Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = color(0xA9B0BD)
                strokeWidth = 5f
                style = Paint.Style.STROKE
                strokeCap = Paint.Cap.ROUND
            }
        val needlePath =
            Path().apply {
                moveTo(28f, 52f)
                quadTo(160f, 58f, 292f, 60f)
            }
        canvas.drawPath(needlePath, needle)
        canvas.drawCircle(292f, 60f, 7f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = color(0x6B7180) })

        // completed rows
        val rowsCompleted = min(reveal.toInt(), totalRows)
        for (k in 0 until rowsCompleted) {
            val y = fabricY + k * swatchRowH
            drawSwatchRow(canvas, k, steps.getJSONObject(k + 1), y, swatchRowH)
        }

        // working row sliding from the needle into place
        val frac = reveal - rowsCompleted
        if (frac > 0.01f && rowsCompleted + 1 < steps.length()) {
            val slotY = fabricY + rowsCompleted * swatchRowH
            val midX = (swX0 + swX1) / 2f
            val dy = (1f - frac) * (swatchNeedleY(midX) - slotY)
            canvas.save()
            canvas.translate(0f, dy)
            paint.alpha = (0.35f + 0.65f * frac).coerceIn(0f, 1f).let { (it * 255).toInt() }
            drawSwatchRow(canvas, rowsCompleted, steps.getJSONObject(rowsCompleted + 1), slotY, swatchRowH)
            paint.alpha = 255
            canvas.restore()
        }

        // live stitches on the needle
        val liveN = steps.getJSONObject(min(index, steps.length() - 1)).optInt("n", 0)
        val lw = (swX1 - swX0) / max(liveN, 1)
        val loop =
            Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = color(0x7C55B0)
                strokeWidth = 2.2f
                style = Paint.Style.STROKE
                strokeCap = Paint.Cap.ROUND
            }
        for (i in 0 until liveN) {
            val x = swX0 + (i + 0.5f) * lw
            val ny = swatchNeedleY(x)
            val p =
                Path().apply {
                    moveTo(x - 3.5f, ny)
                    quadTo(x - 4f, ny + 9f, x, ny + 9f)
                    quadTo(x + 4f, ny + 9f, x + 3.5f, ny)
                }
            canvas.drawPath(p, loop)
        }

        canvas.restore()
    }
}
