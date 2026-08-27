package org.pyknit.android.ui

import android.graphics.Rect
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.core.widget.NestedScrollView
import com.google.android.material.R as MR
import com.google.android.material.button.MaterialButton
import com.google.android.material.progressindicator.LinearProgressIndicator
import com.google.android.material.slider.Slider
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import org.json.JSONArray
import org.json.JSONObject
import org.pyknit.android.MainActivity
import org.pyknit.android.R

/**
 * The Knit Simulator screen. The instruction text is the source of truth;
 * the Python engine builds the simulation. This class only presents the
 * steps the engine produced, mirroring the pyscript demo: a status card
 * with progress and counts, a rendered garment, and simple stepping
 * controls.
 */
class SimulatorView(private val activity: MainActivity) {

    private var scrollView: ScrollView? = null
    private var statusCard: LinearLayout? = null
    private var statusContent: LinearLayout? = null

    // Loaded-mode widgets (rebuilt only when the step count changes).
    private var loadedSteps = -1
    private var progressBar: LinearProgressIndicator? = null
    private var stepLabel: TextView? = null
    private var sectionBarRow: LinearLayout? = null
    private var sectionProgressLabel: TextView? = null
    private var rowValue: TextView? = null
    private var stsValue: TextView? = null
    private var sectionValue: TextView? = null
    private var slider: Slider? = null
    private var rowLog: LinearLayout? = null
    private var rowLogScroller: NestedScrollView? = null
    private var playButton: MaterialButton? = null

    private var garmentView: GarmentView? = null
    private var opPill: TextView? = null

    fun build(): View {
        val c = activity.column()
        c.addView(activity.screenTitle(activity.getString(R.string.sim_title)))
        c.addView(activity.screenIntro(activity.getString(R.string.sim_intro)))

        val editorLayout = TextInputLayout(activity, null, MR.attr.textInputOutlinedStyle).apply {
            hint = activity.getString(R.string.sim_instructions_label)
            val edit = TextInputEditText(activity).apply {
                setText(activity.draftInstructions)
                gravity = Gravity.TOP
                setTextSize(14f)
                typeface = MONO_FACE
                setTextIsSelectable(true)
                minLines = 7
                inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE
            }
            addView(edit, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        }
        // Cap the editor height so long planner patterns cannot push the
        // status card and controls off screen; long text scrolls internally.
        c.addView(editorLayout, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, activity.dp(150)))

        val buildButton = activity.filledButton(activity.getString(R.string.sim_build)) {
            val text = editorLayout.editText?.text?.toString().orEmpty()
            activity.draftInstructions = text
            activity.buildSimulation(text)
        }
        c.addView(buildButton, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = activity.dp(6)
        })

        // Status card: progress, section bar, big counts, scrub slider.
        val card = activity.card()
        val content = LinearLayout(activity).apply { orientation = LinearLayout.VERTICAL }
        card.addView(content, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        statusCard = card
        statusContent = content
        c.addView(card, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = activity.dp(14)
        })

        // Garment card: the rendered knitting plus the current operation.
        val garmentCard = activity.card()
        garmentCard.addView(activity.textView(
            activity.getString(R.string.sim_garment_title),
            sizeSp = 12f, typeface = TITLE_FACE, colorAttr = MR.attr.colorOnSurfaceVariant,
        ))
        val garment = GarmentView(activity).apply {
            contentDescription = activity.getString(R.string.sim_garment_desc)
        }
        garmentView = garment
        // The viewBox is 320x340, so a tall view lets the garment fill the
        // card like the web demo's large stage.
        garmentCard.addView(garment, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, activity.dp(340)))
        val pill = TextView(activity).apply {
            setTextSize(14f)
            typeface = TITLE_FACE
            gravity = Gravity.CENTER
            setPadding(activity.dp(14), activity.dp(10), activity.dp(14), activity.dp(10))
            background = activity.rounded(activity.attrColor(MR.attr.colorPrimaryContainer), 22)
            setTextColor(activity.attrColor(MR.attr.colorOnPrimaryContainer))
        }
        opPill = pill
        garmentCard.addView(pill, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = activity.dp(10)
        })
        c.addView(garmentCard, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = activity.dp(10)
        })

        // Controls: big, obvious touch targets for knitting hands.
        val prev = activity.outlinedButton(activity.getString(R.string.sim_previous)) { activity.move(-1) }
        val next = activity.filledButton(activity.getString(R.string.sim_next)) { activity.move(1) }
        val row1 = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL }
        row1.addView(prev, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply { marginEnd = activity.dp(8) })
        row1.addView(next, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        c.addView(row1, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = activity.dp(10)
        })

        val play = activity.tonalButton(activity.getString(R.string.sim_play)) { activity.togglePlay() }
        playButton = play
        val reset = activity.textButton(activity.getString(R.string.sim_reset)) { activity.resetSimulation() }
        val row2 = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL }
        row2.addView(play, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply { marginEnd = activity.dp(8) })
        row2.addView(reset, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        c.addView(row2, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = activity.dp(4)
        })

        // Worked rows log (like the demo's step log, kept compact).
        val logCard = activity.card()
        logCard.addView(activity.textView(
            activity.getString(R.string.sim_row_log_title),
            sizeSp = 12f, typeface = TITLE_FACE, colorAttr = MR.attr.colorOnSurfaceVariant,
        ))
        val log = LinearLayout(activity).apply { orientation = LinearLayout.VERTICAL }
        rowLog = log
        val scroller = NestedScrollView(activity).apply {
            isVerticalScrollBarEnabled = true
            addView(log)
        }
        rowLogScroller = scroller
        logCard.addView(scroller, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, activity.dp(150)).apply {
            topMargin = activity.dp(2)
        })
        c.addView(logCard, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = activity.dp(10)
        })

        scrollView = ScrollView(activity).apply {
            isFillViewport = true
            addView(activity.maxWidthFrame(c))
        }
        refresh()
        return scrollView!!
    }

    /** Re-render the status card and garment from the activity's state. */
    fun refresh() {
        val sim = activity.simulation
        val content = statusContent ?: return
        if (sim == null) { showEmpty(); return }
        val steps = sim.optJSONArray("steps") ?: run { showEmpty(); return }
        val total = steps.length()
        if (total == 0) { showEmpty(); return }

        val index = activity.simulationIndex.coerceIn(0, total - 1)
        activity.simulationIndex = index
        val step = steps.getJSONObject(index)

        if (loadedSteps != total) buildLoaded(sim, total, steps)

        val denom = (total - 1).coerceAtLeast(1)
        progressBar?.setProgressCompat(index * 100 / denom, true)
        stepLabel?.text = activity.getString(R.string.sim_step_of, index + 1, total)

        val sections = sim.optJSONArray("sections")
        if (sections != null && sections.length() > 0) {
            updateSectionBar(sections, index, step)
            sectionBarRow?.visibility = View.VISIBLE
            sectionProgressLabel?.visibility = View.VISIBLE
        } else {
            sectionBarRow?.visibility = View.GONE
            sectionProgressLabel?.visibility = View.GONE
        }

        val castOn = step.optString("kind") == "cast_on"
        rowValue?.text = if (castOn) activity.getString(R.string.sim_cast_on, step.optInt("n", 0)) else step.optInt("row", 0).toString()
        stsValue?.text = step.optInt("n", 0).toString()
        sectionValue?.text = sectionLabel(sim, step)
        slider?.value = index.toFloat()
        updateRowLog(steps, index)
        playButton?.text = activity.getString(if (activity.playing) R.string.sim_pause else R.string.sim_play)

        opPill?.text = when {
            castOn -> activity.getString(R.string.sim_now, activity.getString(R.string.sim_cast_on, step.optInt("n", 0)))
            index >= total - 1 -> activity.getString(R.string.sim_end)
            else -> activity.getString(R.string.sim_now, step.optString("op"))
        }
        garmentView?.setSimulation(sim, steps, index)
    }

    fun showError(message: String) {
        val content = statusContent ?: return
        loadedSteps = -1
        content.removeAllViews()
        val card = activity.card()
        card.background = activity.rounded(activity.attrColor(MR.attr.colorErrorContainer), 12)
        card.addView(activity.textView(
            "${activity.getString(R.string.sim_error)}: $message",
            sizeSp = 14f, colorAttr = MR.attr.colorOnErrorContainer,
        ))
        content.addView(card)
        opPill?.text = ""
        garmentView?.setSimulation(null, JSONArray(), 0, animate = false)
    }

    private fun showEmpty() {
        val content = statusContent ?: return
        loadedSteps = -1
        content.removeAllViews()
        val wrap = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(activity.dp(4), activity.dp(6), activity.dp(4), activity.dp(6))
        }
        wrap.addView(activity.textView(
            activity.getString(R.string.sim_empty_title),
            sizeSp = 16f, typeface = TITLE_FACE,
        ))
        wrap.addView(activity.textView(
            activity.getString(R.string.sim_empty_body),
            sizeSp = 13.5f, colorAttr = MR.attr.colorOnSurfaceVariant,
        ))
        content.addView(wrap)
        playButton?.text = activity.getString(R.string.sim_play)
        opPill?.text = ""
        garmentView?.setSimulation(null, JSONArray(), 0, animate = false)
    }

    private fun buildLoaded(sim: JSONObject, total: Int, steps: JSONArray) {
        val content = statusContent ?: return
        loadedSteps = total
        content.removeAllViews()

        // Progress
        val progress = LinearProgressIndicator(activity, null, MR.attr.linearProgressIndicatorStyle).apply {
            isIndeterminate = false
            max = 100
            trackColor = activity.attrColor(MR.attr.colorSurfaceVariant)
        }
        progressBar = progress
        content.addView(progress, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, activity.dp(6)))

        val stepLabelView = activity.textView("", sizeSp = 12f, colorAttr = MR.attr.colorOnSurfaceVariant)
        stepLabel = stepLabelView
        content.addView(stepLabelView, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = activity.dp(4)
        })

        // Section segments
        val sectionRow = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL }
        sectionBarRow = sectionRow
        content.addView(sectionRow, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = activity.dp(8)
        })
        val sectionProgress = activity.textView("", sizeSp = 12f, colorAttr = MR.attr.colorOnSurfaceVariant)
        sectionProgressLabel = sectionProgress
        content.addView(sectionProgress, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = activity.dp(2)
        })

        // Big stats: Row | Stitches | Section
        val stats = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL }
        val rowBlock = activity.statBlock("", activity.getString(R.string.sim_stat_row))
        val stsBlock = activity.statBlock("", activity.getString(R.string.sim_stat_stitches))
        val sectionBlock = activity.statBlock("", activity.getString(R.string.sim_stat_section))
        rowValue = rowBlock.getChildAt(0) as TextView
        stsValue = stsBlock.getChildAt(0) as TextView
        sectionValue = sectionBlock.getChildAt(0) as TextView
        listOf(rowBlock, stsBlock, sectionBlock).forEachIndexed { i, block ->
            stats.addView(block, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply {
                if (i < 2) marginEnd = activity.dp(6)
            })
        }
        content.addView(stats, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = activity.dp(10)
        })

        // Scrub slider
        val scrub = Slider(activity, null, MR.attr.sliderStyle).apply {
            valueFrom = 0f
            valueTo = (total - 1).toFloat()
            stepSize = 1f
            contentDescription = activity.getString(R.string.sim_scrub_desc)
            setLabelFormatter { value -> activity.getString(R.string.sim_step_of, value.toInt() + 1, total) }
            addOnChangeListener { _, value, fromUser ->
                if (fromUser) activity.moveTo(value.toInt())
            }
        }
        slider = scrub
        content.addView(scrub, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = activity.dp(6)
        })
    }

    private fun updateSectionBar(sections: JSONArray, index: Int, step: JSONObject) {
        val row = sectionBarRow ?: return
        row.removeAllViews()
        for (i in 0 until sections.length()) {
            val sec = sections.getJSONObject(i)
            val start = sec.getInt("start")
            val end = sec.getInt("end")
            val active = index in start until end
            val segment = View(activity).apply {
                background = activity.rounded(
                    if (active) activity.colorPrimary else activity.attrColor(MR.attr.colorSurfaceVariant), 4,
                )
            }
            row.addView(segment, LinearLayout.LayoutParams(0, activity.dp(8), (end - start).toFloat()).apply {
                marginEnd = activity.dp(3)
            })
        }
        val sec = sectionAt(sections, index)
        sectionProgressLabel?.text = activity.getString(
            R.string.sim_progress_in_section,
            step.optInt("sec_row", 1),
            step.optInt("sec_rows", 0),
            sec.optString("label"),
        )
    }

    private fun sectionAt(sections: JSONArray, index: Int): JSONObject {
        for (i in 0 until sections.length()) {
            val sec = sections.getJSONObject(i)
            if (index in sec.getInt("start") until sec.getInt("end")) return sec
        }
        return sections.getJSONObject(sections.length() - 1)
    }

    private fun sectionLabel(sim: JSONObject, step: JSONObject): String {
        val explicit = step.optString("section_label")
        if (explicit.isNotEmpty()) return explicit
        return if (sim.optString("garment") == "sweater") "Manual pattern"
        else sim.optString("garment").replaceFirstChar { it.uppercase() }
    }

    private fun updateRowLog(steps: JSONArray, index: Int) {
        val log = rowLog ?: return
        val scroller = rowLogScroller ?: return
        log.removeAllViews()
        if (index <= 0) {
            log.addView(activity.textView(
                activity.getString(R.string.sim_row_log_empty),
                sizeSp = 13f, colorAttr = MR.attr.colorOnSurfaceVariant,
            ))
            return
        }
        val start = (index - 12).coerceAtLeast(0)
        for (i in start until index) {
            val st = steps.getJSONObject(i)
            val text = if (st.optString("kind") == "cast_on") {
                activity.getString(R.string.sim_cast_on, st.optInt("n", 0))
            } else {
                "Row ${st.optInt("row")}: ${st.optString("op")}"
            }
            val last = i == index - 1
            log.addView(activity.textView(
                text,
                sizeSp = 13f,
                typeface = MONO_FACE,
                colorAttr = if (last) MR.attr.colorOnSurface else MR.attr.colorOnSurfaceVariant,
                lineSpacing = 1.15f,
            ))
        }
        scroller.post { scroller.fullScroll(View.FOCUS_DOWN) }
    }

    /** Scroll the outer page so the status card is visible (after a Build). */
    fun bringStatusIntoView() {
        val sv = scrollView ?: return
        val card = statusCard ?: return
        sv.post {
            val rect = Rect(0, 0, card.width, card.height)
            card.requestRectangleOnScreen(rect, false)
        }
    }
}
