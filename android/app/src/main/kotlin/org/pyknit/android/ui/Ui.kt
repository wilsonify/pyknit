package org.pyknit.android.ui

import android.content.Context
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import com.google.android.material.button.MaterialButton
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import com.google.android.material.R as MR

// ---------- density & theme resolution ----------

fun Context.dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

fun Context.attrColor(attr: Int): Int {
    val value = TypedValue()
    return if (theme.resolveAttribute(attr, value, true)) {
        value.data
    } else {
        0xFF000000.toInt()
    }
}

val Context.colorPrimary: Int get() = attrColor(MR.attr.colorPrimary)
val Context.colorOnPrimary: Int get() = attrColor(MR.attr.colorOnPrimary)
val Context.colorPrimaryContainer: Int get() = attrColor(MR.attr.colorPrimaryContainer)
val Context.colorOnPrimaryContainer: Int get() = attrColor(MR.attr.colorOnPrimaryContainer)
val Context.colorBackground: Int get() = attrColor(android.R.attr.colorBackground)
val Context.colorOnBackground: Int get() = attrColor(MR.attr.colorOnBackground)
val Context.colorSurface: Int get() = attrColor(MR.attr.colorSurface)
val Context.colorOnSurface: Int get() = attrColor(MR.attr.colorOnSurface)
val Context.colorSurfaceVariant: Int get() = attrColor(MR.attr.colorSurfaceVariant)
val Context.colorOnSurfaceVariant: Int get() = attrColor(MR.attr.colorOnSurfaceVariant)
val Context.colorOutlineVariant: Int get() = attrColor(MR.attr.colorOutlineVariant)
val Context.colorError: Int get() = attrColor(MR.attr.colorError)
val Context.colorErrorContainer: Int get() = attrColor(MR.attr.colorErrorContainer)
val Context.colorOnErrorContainer: Int get() = attrColor(MR.attr.colorOnErrorContainer)
val Context.colorSuccess: Int get() = getColor(org.pyknit.android.R.color.success)
val Context.colorSuccessContainer: Int get() = getColor(org.pyknit.android.R.color.success_container)
val Context.colorOnSuccessContainer: Int get() = getColor(org.pyknit.android.R.color.on_success_container)
val Context.isWideScreen: Boolean get() = resources.configuration.screenWidthDp >= 600

// Typography: keep the platform font families so font scaling behaves natively.
val TITLE_FACE: Typeface = Typeface.create("sans-serif-medium", Typeface.NORMAL)
val MONO_FACE: Typeface = Typeface.MONOSPACE

// ---------- primitives ----------

fun Context.rounded(
    fill: Int,
    radiusDp: Int,
    stroke: Int? = null,
): GradientDrawable =
    GradientDrawable().apply {
        cornerRadius = dp(radiusDp).toFloat()
        setColor(fill)
        if (stroke != null) setStroke(dp(1), stroke)
    }

fun Context.textView(
    text: String,
    sizeSp: Float = 14f,
    colorAttr: Int = MR.attr.colorOnSurface,
    typeface: Typeface = Typeface.DEFAULT,
    lineSpacing: Float = 1.25f,
    maxLines: Int = Int.MAX_VALUE,
): TextView =
    TextView(this).apply {
        this.text = text
        setTextSize(sizeSp)
        setTextColor(attrColor(colorAttr))
        setLineSpacing(0f, lineSpacing)
        setPadding(dp(2), dp(2), dp(2), dp(2))
        this.typeface = typeface
        this.maxLines = maxLines
        ellipsize = android.text.TextUtils.TruncateAt.END
    }

/** Small uppercase kicker that groups a screen into sections. */
fun Context.sectionHeader(text: String): TextView =
    TextView(this).apply {
        this.text = text.uppercase()
        setTextSize(12f)
        letterSpacing = 0.12f
        setTextColor(attrColor(MR.attr.colorPrimary))
        typeface = TITLE_FACE
        setPadding(dp(2), dp(14), dp(2), dp(2))
    }

fun Context.screenTitle(text: String): TextView = textView(text, sizeSp = 24f, typeface = TITLE_FACE)

fun Context.screenIntro(text: String): TextView = textView(text, sizeSp = 14f, colorAttr = MR.attr.colorOnSurfaceVariant)

fun Context.hairline(): View =
    View(this).apply {
        setBackgroundColor(attrColor(MR.attr.colorOutlineVariant))
        minimumHeight = dp(1)
    }

// ---------- cards & containers ----------

/** Rounded surface card with a hairline border. */
fun Context.card(
    paddingDp: Int = 16,
    radiusDp: Int = 12,
): LinearLayout =
    LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        background = rounded(attrColor(MR.attr.colorSurface), radiusDp, stroke = attrColor(MR.attr.colorOutlineVariant))
        setPadding(dp(paddingDp), dp(paddingDp), dp(paddingDp), dp(paddingDp))
    }

/** Column with the standard screen gutters. */
fun Context.column(): LinearLayout =
    LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(16), dp(8), dp(16), dp(28))
    }

/** Constrains content to a readable measure on large screens and centers it. */
fun Context.maxWidthFrame(inner: View): FrameLayout =
    FrameLayout(this).apply {
        setBackgroundColor(attrColor(android.R.attr.colorBackground))
        val max = dp(640)
        val width = minOf(max, resources.displayMetrics.widthPixels)
        addView(inner, FrameLayout.LayoutParams(width, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER_HORIZONTAL))
    }

/** A compact vertical stat block: big value over a small label. */
fun Context.statBlock(
    value: String,
    label: String,
): LinearLayout =
    LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        gravity = Gravity.CENTER_HORIZONTAL
        background = rounded(attrColor(MR.attr.colorSurfaceVariant), dp(10))
        setPadding(dp(10), dp(10), dp(10), dp(8))
        addView(
            textView(value, sizeSp = 20f, typeface = TITLE_FACE, lineSpacing = 1.1f),
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                gravity = Gravity.CENTER_HORIZONTAL
            },
        )
        addView(
            textView(label, sizeSp = 11f, colorAttr = MR.attr.colorOnSurfaceVariant, lineSpacing = 1.1f),
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                gravity = Gravity.CENTER_HORIZONTAL
            },
        )
    }

// ---------- buttons ----------

fun Context.filledButton(
    label: String,
    action: () -> Unit,
): MaterialButton =
    MaterialButton(this, null, MR.attr.materialButtonStyle).apply {
        text = label
        isAllCaps = false
        setOnClickListener { action() }
    }

fun Context.outlinedButton(
    label: String,
    action: () -> Unit,
): MaterialButton =
    MaterialButton(this, null, MR.attr.materialButtonOutlinedStyle).apply {
        text = label
        isAllCaps = false
        setOnClickListener { action() }
    }

fun Context.tonalButton(
    label: String,
    action: () -> Unit,
): MaterialButton =
    MaterialButton(android.view.ContextThemeWrapper(this, MR.style.Widget_Material3_Button_TonalButton), null, 0).apply {
        text = label
        isAllCaps = false
        setOnClickListener { action() }
    }

fun Context.textButton(
    label: String,
    action: () -> Unit,
): MaterialButton =
    MaterialButton(android.view.ContextThemeWrapper(this, MR.style.Widget_Material3_Button_TextButton), null, 0).apply {
        text = label
        isAllCaps = false
        setOnClickListener { action() }
    }

// ---------- inputs ----------

/** Outlined text field with a floating label and optional unit helper. */
fun Context.inputField(
    hint: String,
    value: String,
    numeric: Boolean,
    helper: String? = null,
): TextInputLayout =
    TextInputLayout(this, null, MR.attr.textInputOutlinedStyle).apply {
        isHintEnabled = true
        if (helper != null) helperText = helper
        val edit =
            TextInputEditText(this@inputField).apply {
                setText(value)
                setHint(hint)
                setTextSize(16f)
                setInputType(
                    if (numeric) {
                        android.text.InputType.TYPE_CLASS_NUMBER or android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL
                    } else {
                        android.text.InputType.TYPE_CLASS_TEXT
                    },
                )
            }
        addView(edit, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
    }

/** Read-only dropdown built from label -> key pairs; the key is what Python receives. */
fun Context.choiceField(
    hint: String,
    selectedKey: String,
    choices: List<Pair<String, String>>,
): TextInputLayout =
    TextInputLayout(this, null, MR.attr.textInputOutlinedExposedDropdownMenuStyle).apply {
        isHintEnabled = true
        val edit =
            com.google.android.material.textfield.MaterialAutoCompleteTextView(this@choiceField).apply {
                setHint(hint)
                setTextSize(16f)
                setSimpleItems(choices.map { it.first }.toTypedArray())
                setText(choices.firstOrNull { it.second == selectedKey }?.first ?: selectedKey, false)
                // Dropdown-only: selections, not free typing.
                setKeyListener(null)
                isFocusable = true
                isFocusableInTouchMode = true
            }
        addView(edit, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
    }
