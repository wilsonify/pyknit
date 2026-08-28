package org.pyknit.android.ui

import android.graphics.Rect
import android.graphics.drawable.GradientDrawable
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.core.widget.NestedScrollView
import com.google.android.material.button.MaterialButton
import com.google.android.material.progressindicator.LinearProgressIndicator
import com.google.android.material.slider.Slider
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import org.json.JSONArray
import org.json.JSONObject
import org.pyknit.android.MainActivity
import org.pyknit.android.R
import com.google.android.material.R as MR

/**
 * The Knit Simulator screen. The instruction text is the source of truth;
 * the Python engine builds the simulation. This class only presents the
 * steps the engine produced, mirroring the pyscript demo: a status card
 * with progress and counts, a rendered garment, and simple stepping
 * controls.
 *
 * Improvements over the pyscript demo:
 * - Speed selector (Slow / Normal / Fast) for play-through
 * - Section progress pills showing done / active / pending sections
 * - Phase line showing current section and row progress
 * - Gradient garment stage background
 * - Collapsible row log
 * - Plan banner when loaded from a planner
 */
class SimulatorView(private val activity: MainActivity) {
    private var scrollView: ScrollView? = null
    private var statusCard: LinearLayout? = null
    private var statusContent: LinearLayout? = null

    // Loaded-mode widgets (rebuilt only when the step count changes).
    private var loadedSteps = -1
    private var progressBar: LinearProgressIndicator? = null
    private var stepLabel: TextView? = null
    private var phaseLine: TextView? = null
    private var sectionBarRow: LinearLayout? = null
    private var sectionPillsRow: LinearLayout? = null
    private var sectionProgressLabel: TextView? = null
    private var rowValue: TextView? = null
    private var stsValue: TextView? = null
    private var sectionValue: TextView? = null
    private var slider: Slider? = null
    private var rowLog: LinearLayout? = null
    private var rowLogScroller: NestedScrollView? = null
    private var rowLogToggle: MaterialButton? = null
    private var playButton: MaterialButton? = null
    private var speedButton: MaterialButton? = null
    private var planBanner: TextView? = null

    private var garmentView: GarmentView? = null
    private var opPill: TextView? = null

    private var logExpanded = false

    fun build(): View {
        val c = activity.column()
        c.addView(activity.screenTitle(activity.getString(R.string.sim_title)))
        c.addView(activity.screenIntro(activity.getString(R.string.sim_intro)))

        val editorLayout =
            TextInputLayout(activity, null, MR.attr.textInputOutlinedStyle).apply {
                hint = activity.getString(R.string.sim_instructions_label)
                val edit =
                    TextInputEditText(activity).apply {
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

        val buildButton =
            activity.filledButton(activity.getString(R.string.sim_build)) {
                val text = editorLayout.editText?.text?.toString().orEmpty()
                activity.draftInstructions = text
                activity.buildSimulation(text)
            }
        c.addView(
            buildButton,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(6)
            },
        )

        // Plan banner — shown when a planner pattern is loaded.
        val banner =
            TextView(activity).apply {
                setTextSize(13f)
                typeface = TITLE_FACE
                gravity = Gravity.CENTER
                visibility = View.GONE
            }
        planBanner = banner
        c.addView(
            banner,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(8)
            },
        )

        // Status card: progress, section bar, big counts, scrub slider.
        val card = activity.card()
        val content = LinearLayout(activity).apply { orientation = LinearLayout.VERTICAL }
        card.addView(content, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        statusCard = card
        statusContent = content
        c.addView(
            card,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(14)
            },
        )

        // Garment card: gradient background, the rendered knitting, and the operation.
        val garmentCard =
            FrameLayout(activity).apply {
                background =
                    GradientDrawable(
                        GradientDrawable.Orientation.TOP_BOTTOM,
                        intArrayOf(
                            activity.attrColor(MR.attr.colorSurface),
                            activity.attrColor(MR.attr.colorSurfaceVariant),
                        ),
                    ).apply {
                        cornerRadius = activity.dp(12).toFloat()
                        setStroke(activity.dp(1), activity.attrColor(MR.attr.colorOutlineVariant))
                    }
                setPadding(activity.dp(16), activity.dp(14), activity.dp(16), activity.dp(14))
            }
        val garmentInner = LinearLayout(activity).apply { orientation = LinearLayout.VERTICAL }
        garmentInner.addView(
            activity.textView(
                activity.getString(R.string.sim_garment_title),
                sizeSp = 12f,
                typeface = TITLE_FACE,
                colorAttr = MR.attr.colorOnSurfaceVariant,
            ),
        )
        val garment =
            GarmentView(activity).apply {
                contentDescription = activity.getString(R.string.sim_garment_desc)
            }
        garmentView = garment
        // The viewBox is 320x340, so a tall view lets the garment fill the
        // card like the web demo's large stage.
        garmentInner.addView(garment, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, activity.dp(340)))
        val pill =
            TextView(activity).apply {
                setTextSize(14f)
                typeface = TITLE_FACE
                gravity = Gravity.CENTER
                setPadding(activity.dp(14), activity.dp(10), activity.dp(14), activity.dp(10))
                background = activity.rounded(activity.attrColor(MR.attr.colorPrimaryContainer), 22)
                setTextColor(activity.attrColor(MR.attr.colorOnPrimaryContainer))
            }
        opPill = pill
        garmentInner.addView(
            pill,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(10)
            },
        )
        garmentCard.addView(
            garmentInner,
            FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT),
        )
        c.addView(
            garmentCard,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(10)
            },
        )

        // Controls: big, obvious touch targets for knitting hands.
        val prev = activity.outlinedButton(activity.getString(R.string.sim_previous)) { activity.move(-1) }
        val next = activity.filledButton(activity.getString(R.string.sim_next)) { activity.move(1) }
        val row1 = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL }
        row1.addView(prev, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply { marginEnd = activity.dp(8) })
        row1.addView(next, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        c.addView(
            row1,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(10)
            },
        )

        val play = activity.tonalButton(activity.getString(R.string.sim_play)) { activity.togglePlay() }
        playButton = play
        val speed = activity.outlinedButton(speedLabel()) { cycleSpeed() }
        speedButton = speed
        val reset = activity.textButton(activity.getString(R.string.sim_reset)) { activity.resetSimulation() }
        val row2 = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL }
        row2.addView(play, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply { marginEnd = activity.dp(6) })
        row2.addView(speed, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply { marginEnd = activity.dp(6) })
        row2.addView(reset, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        c.addView(
            row2,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(4)
            },
        )

        // Worked rows log — collapsible, matching the demo's <details> toggle.
        val logCard = activity.card()
        val logHeader =
            LinearLayout(activity).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                isClickable = true
                isFocusable = true
                setOnClickListener { toggleLog() }
            }
        logHeader.addView(
            activity.textView(
                activity.getString(R.string.sim_row_log_title),
                sizeSp = 12f,
                typeface = TITLE_FACE,
                colorAttr = MR.attr.colorOnSurfaceVariant,
            ),
            LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f),
        )
        logHeader.addView(
            activity.textView(
                "",
                // will be updated by toggleLog
                sizeSp = 12f,
                colorAttr = MR.attr.colorPrimary,
            ),
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT),
        )
        logCard.addView(logHeader, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        val log = LinearLayout(activity).apply { orientation = LinearLayout.VERTICAL }
        rowLog = log
        val scroller =
            NestedScrollView(activity).apply {
                isVerticalScrollBarEnabled = true
                visibility = View.GONE
                addView(log)
            }
        rowLogScroller = scroller
        logCard.addView(
            scroller,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, activity.dp(150)).apply {
                topMargin = activity.dp(2)
            },
        )
        rowLogToggle = logHeader.getChildAt(1) as? MaterialButton // not actually a button, but tracks state
        c.addView(
            logCard,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(10)
            },
        )

        scrollView =
            ScrollView(activity).apply {
                isFillViewport = true
                addView(activity.maxWidthFrame(c))
            }
        toggleLog() // set initial toggle text
        refresh()
        return scrollView!!
    }

    // ---------- speed ----------

    private fun speedLabel(): String =
        when {
            activity.speedMultiplier < 0.7f -> activity.getString(R.string.sim_speed_slow)
            activity.speedMultiplier > 1.5f -> activity.getString(R.string.sim_speed_fast)
            else -> activity.getString(R.string.sim_speed_normal)
        }

    private fun cycleSpeed() {
        activity.speedMultiplier =
            when {
                activity.speedMultiplier < 0.7f -> 1.0f // slow -> normal
                activity.speedMultiplier < 1.5f -> 2.0f // normal -> fast
                else -> 0.5f // fast -> slow
            }
        speedButton?.text = speedLabel()
    }

    // ---------- log toggle ----------

    private fun toggleLog() {
        logExpanded = !logExpanded
        rowLogScroller?.visibility = if (logExpanded) View.VISIBLE else View.GONE
        // Update the toggle hint text via the parent card's last child
        val parent = rowLogScroller?.parent as? ViewGroup ?: return
        val hint = parent.getChildAt(0) as? LinearLayout ?: return
        val toggle = hint.getChildAt(1) as? TextView ?: return
        toggle.text = if (logExpanded) activity.getString(R.string.sim_row_log_hide) else activity.getString(R.string.sim_row_log_show)
    }

    // ---------- refresh ----------

    /** Re-render the status card and garment from the activity's state. */
    fun refresh() {
        val sim = activity.simulation
        val content = statusContent ?: return
        if (sim == null) {
            showEmpty()
            return
        }
        val steps =
            sim.optJSONArray("steps") ?: run {
                showEmpty()
                return
            }
        val total = steps.length()
        if (total == 0) {
            showEmpty()
            return
        }

        val index = activity.simulationIndex.coerceIn(0, total - 1)
        activity.simulationIndex = index
        val step = steps.getJSONObject(index)

        if (loadedSteps != total) buildLoaded(sim, total, steps)

        // Plan banner
        updatePlanBanner()

        val denom = (total - 1).coerceAtLeast(1)
        progressBar?.setProgressCompat(index * 100 / denom, true)
        stepLabel?.text = activity.getString(R.string.sim_step_of, index + 1, total)

        val sections = sim.optJSONArray("sections")
        if (sections != null && sections.length() > 0) {
            updateSectionBar(sections, index, step)
            updateSectionPills(sections, index)
            updatePhaseLine(sections, index, step)
            sectionPillsRow?.visibility = View.VISIBLE
            phaseLine?.visibility = View.VISIBLE
        } else {
            sectionPillsRow?.visibility = View.GONE
            phaseLine?.visibility = View.GONE
        }

        val castOn = step.optString("kind") == "cast_on"
        rowValue?.text = if (castOn) activity.getString(R.string.sim_cast_on, step.optInt("n", 0)) else step.optInt("row", 0).toString()
        stsValue?.text = step.optInt("n", 0).toString()
        sectionValue?.text = sectionLabel(sim, step)
        slider?.value = index.toFloat()
        if (logExpanded) updateRowLog(steps, index)
        playButton?.text = activity.getString(if (activity.playing) R.string.sim_pause else R.string.sim_play)

        opPill?.text =
            when {
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
        card.addView(
            activity.textView(
                "${activity.getString(R.string.sim_error)}: $message",
                sizeSp = 14f,
                colorAttr = MR.attr.colorOnErrorContainer,
            ),
        )
        content.addView(card)
        opPill?.text = ""
        garmentView?.setSimulation(null, JSONArray(), 0, animate = false)
    }

    private fun showEmpty() {
        val content = statusContent ?: return
        loadedSteps = -1
        content.removeAllViews()
        val wrap =
            LinearLayout(activity).apply {
                orientation = LinearLayout.VERTICAL
                gravity = Gravity.CENTER_HORIZONTAL
                setPadding(activity.dp(4), activity.dp(6), activity.dp(4), activity.dp(6))
            }
        wrap.addView(
            activity.textView(
                activity.getString(R.string.sim_empty_title),
                sizeSp = 16f,
                typeface = TITLE_FACE,
            ),
        )
        wrap.addView(
            activity.textView(
                activity.getString(R.string.sim_empty_body),
                sizeSp = 13.5f,
                colorAttr = MR.attr.colorOnSurfaceVariant,
            ),
        )
        content.addView(wrap)
        playButton?.text = activity.getString(R.string.sim_play)
        opPill?.text = ""
        garmentView?.setSimulation(null, JSONArray(), 0, animate = false)
    }

    private fun buildLoaded(
        sim: JSONObject,
        total: Int,
        steps: JSONArray,
    ) {
        val content = statusContent ?: return
        loadedSteps = total
        content.removeAllViews()

        // Progress
        val progress =
            LinearProgressIndicator(activity, null, MR.attr.linearProgressIndicatorStyle).apply {
                isIndeterminate = false
                max = 100
                trackColor = activity.attrColor(MR.attr.colorSurfaceVariant)
            }
        progressBar = progress
        content.addView(progress, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, activity.dp(6)))

        val stepLabelView = activity.textView("", sizeSp = 12f, colorAttr = MR.attr.colorOnSurfaceVariant)
        stepLabel = stepLabelView
        content.addView(
            stepLabelView,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(4)
            },
        )

        // Phase line (like demo's bold phase-line box)
        val phase =
            TextView(activity).apply {
                setTextSize(14f)
                typeface = TITLE_FACE
                setPadding(activity.dp(10), activity.dp(6), activity.dp(10), activity.dp(6))
                background = activity.rounded(activity.attrColor(MR.attr.colorSurfaceVariant), 8)
                visibility = View.GONE
            }
        phaseLine = phase
        content.addView(
            phase,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(6)
            },
        )

        // Section color bar
        val sectionRow = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL }
        sectionBarRow = sectionRow
        content.addView(
            sectionRow,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(8)
            },
        )

        // Section pills (done / active / pending)
        val pillsRow =
            LinearLayout(activity).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.START
            }
        sectionPillsRow = pillsRow
        content.addView(
            pillsRow,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(6)
            },
        )

        val sectionProgress = activity.textView("", sizeSp = 12f, colorAttr = MR.attr.colorOnSurfaceVariant)
        sectionProgressLabel = sectionProgress
        content.addView(
            sectionProgress,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(2)
            },
        )

        // Big stats: Row | Stitches | Section
        val stats = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL }
        val rowBlock = activity.statBlock("", activity.getString(R.string.sim_stat_row))
        val stsBlock = activity.statBlock("", activity.getString(R.string.sim_stat_stitches))
        val sectionBlock = activity.statBlock("", activity.getString(R.string.sim_stat_section))
        rowValue = rowBlock.getChildAt(0) as TextView
        stsValue = stsBlock.getChildAt(0) as TextView
        sectionValue = sectionBlock.getChildAt(0) as TextView
        listOf(rowBlock, stsBlock, sectionBlock).forEachIndexed { i, block ->
            stats.addView(
                block,
                LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply {
                    if (i < 2) marginEnd = activity.dp(6)
                },
            )
        }
        content.addView(
            stats,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(10)
            },
        )

        // Scrub slider
        val scrub =
            Slider(activity, null, MR.attr.sliderStyle).apply {
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
        content.addView(
            scrub,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(6)
            },
        )
    }

    // ---------- section bar ----------

    private fun updateSectionBar(
        sections: JSONArray,
        index: Int,
        step: JSONObject,
    ) {
        val row = sectionBarRow ?: return
        row.removeAllViews()
        for (i in 0 until sections.length()) {
            val sec = sections.getJSONObject(i)
            val start = sec.getInt("start")
            val end = sec.getInt("end")
            val active = index in start until end
            val segment =
                View(activity).apply {
                    background =
                        activity.rounded(
                            if (active) activity.colorPrimary else activity.attrColor(MR.attr.colorSurfaceVariant),
                            4,
                        )
                }
            row.addView(
                segment,
                LinearLayout.LayoutParams(0, activity.dp(8), (end - start).toFloat()).apply {
                    marginEnd = activity.dp(3)
                },
            )
        }
        val sec = sectionAt(sections, index)
        sectionProgressLabel?.text =
            activity.getString(
                R.string.sim_progress_in_section,
                step.optInt("sec_row", 1),
                step.optInt("sec_rows", 0),
                sec.optString("label"),
            )
    }

    // ---------- section pills ----------

    private fun updateSectionPills(
        sections: JSONArray,
        index: Int,
    ) {
        val row = sectionPillsRow ?: return
        row.removeAllViews()
        val currentSection = sectionAt(sections, index)
        for (i in 0 until sections.length()) {
            val sec = sections.getJSONObject(i)
            val start = sec.getInt("start")
            val end = sec.getInt("end")
            val done = index >= end
            val active = index in start until end
            val label = sec.optString("label")
            if (label.isEmpty()) continue

            val pillBg: Int
            val pillText: Int
            val pillBorder: Int
            when {
                done -> {
                    pillBg = activity.colorSuccess
                    pillText = 0xFFFFFFFF.toInt()
                    pillBorder = activity.colorSuccess
                }
                active -> {
                    pillBg = activity.attrColor(MR.attr.colorPrimaryContainer)
                    pillText = activity.attrColor(MR.attr.colorOnPrimaryContainer)
                    pillBorder = activity.colorPrimary
                }
                else -> {
                    pillBg = activity.attrColor(MR.attr.colorSurfaceVariant)
                    pillText = activity.attrColor(MR.attr.colorOnSurfaceVariant)
                    pillBorder = activity.attrColor(MR.attr.colorOutlineVariant)
                }
            }
            val pill =
                TextView(activity).apply {
                    text = if (done) "✓ $label" else label
                    setTextSize(11f)
                    typeface = TITLE_FACE
                    setTextColor(pillText)
                    setPadding(activity.dp(10), activity.dp(4), activity.dp(10), activity.dp(4))
                    background =
                        GradientDrawable().apply {
                            setColor(pillBg)
                            cornerRadius = activity.dp(10).toFloat()
                            setStroke(activity.dp(1), pillBorder)
                        }
                }
            row.addView(
                pill,
                LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT,
                ).apply { marginEnd = activity.dp(6) },
            )
        }
    }

    // ---------- phase line ----------

    private fun updatePhaseLine(
        sections: JSONArray,
        index: Int,
        step: JSONObject,
    ) {
        val line = phaseLine ?: return
        val sec = sectionAt(sections, index)
        val label = sec.optString("label")
        val secRow = step.optInt("sec_row", 1)
        val secRows = step.optInt("sec_rows", 0)
        line.text =
            if (label.isNotEmpty() && secRows > 0) {
                activity.getString(R.string.sim_phase, label, secRow, secRows)
            } else {
                activity.getString(R.string.sim_step_of, index + 1, sections.getJSONObject(sections.length() - 1).getInt("end"))
            }
    }

    // ---------- plan banner ----------

    private fun updatePlanBanner() {
        val banner = planBanner ?: return
        val label = activity.plannerLabel
        if (label != null) {
            banner.text = activity.getString(R.string.sim_plan_loaded, label)
            banner.background = activity.rounded(activity.attrColor(MR.attr.colorPrimaryContainer), 8)
            banner.setTextColor(activity.attrColor(MR.attr.colorOnPrimaryContainer))
            banner.visibility = View.VISIBLE
        } else {
            banner.visibility = View.GONE
        }
    }

    // ---------- helpers ----------

    private fun sectionAt(
        sections: JSONArray,
        index: Int,
    ): JSONObject {
        for (i in 0 until sections.length()) {
            val sec = sections.getJSONObject(i)
            if (index in sec.getInt("start") until sec.getInt("end")) return sec
        }
        return sections.getJSONObject(sections.length() - 1)
    }

    private fun sectionLabel(
        sim: JSONObject,
        step: JSONObject,
    ): String {
        val explicit = step.optString("section_label")
        if (explicit.isNotEmpty()) return explicit
        return if (sim.optString("garment") == "sweater") {
            "Manual pattern"
        } else {
            sim.optString("garment").replaceFirstChar { it.uppercase() }
        }
    }

    private fun updateRowLog(
        steps: JSONArray,
        index: Int,
    ) {
        val log = rowLog ?: return
        val scroller = rowLogScroller ?: return
        log.removeAllViews()
        if (index <= 0) {
            log.addView(
                activity.textView(
                    activity.getString(R.string.sim_row_log_empty),
                    sizeSp = 13f,
                    colorAttr = MR.attr.colorOnSurfaceVariant,
                ),
            )
            return
        }
        val start = (index - 12).coerceAtLeast(0)
        for (i in start until index) {
            val st = steps.getJSONObject(i)
            val text =
                if (st.optString("kind") == "cast_on") {
                    activity.getString(R.string.sim_cast_on, st.optInt("n", 0))
                } else {
                    "Row ${st.optInt("row")}: ${st.optString("op")}"
                }
            val last = i == index - 1
            log.addView(
                activity.textView(
                    text,
                    sizeSp = 13f,
                    typeface = MONO_FACE,
                    colorAttr = if (last) MR.attr.colorOnSurface else MR.attr.colorOnSurfaceVariant,
                    lineSpacing = 1.15f,
                ),
            )
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
