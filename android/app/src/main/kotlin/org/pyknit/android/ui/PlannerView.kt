package org.pyknit.android.ui

import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.ScrollView
import org.json.JSONObject
import com.google.android.material.R as MR

/** One input field on a planner screen. `choices` are label -> Python key pairs. */
data class InputSpec(
    val key: String,
    val label: String,
    val default: String,
    val unit: String? = null,
    val choices: List<Pair<String, String>>? = null,
) {
    val isChoice: Boolean get() = choices != null
    val isNumeric: Boolean get() = !isChoice && default.toDoubleOrNull() != null
}

data class PlannerSpec(
    val name: String,
    val title: String,
    val groups: List<Pair<String, List<InputSpec>>>,
    val stats: (JSONObject, JSONObject) -> List<Pair<String, String>>,
)

object PlannerSpecs {
    private fun num(
        json: JSONObject,
        key: String,
    ): String {
        val v = json.opt(key)
        return when (v) {
            is Double -> if (v == v.toLong().toDouble()) v.toLong().toString() else v.toString()
            is Int, is Long -> v.toString()
            else -> json.optString(key)
        }
    }

    private fun thousands(n: Any?): String =
        when (n) {
            is Int -> String.format("%,d", n)
            is Long -> String.format("%,d", n)
            is Double -> String.format("%,.0f", n)
            else -> n?.toString() ?: "—"
        }

    val all: Map<String, PlannerSpec> =
        listOf(
            PlannerSpec(
                name = "raglan",
                title = "Raglan Sweater Planner",
                groups =
                    listOf(
                        "Gauge" to
                            listOf(
                                InputSpec("stitches_per_inch", "Stitches per inch", "5", "st/in"),
                                InputSpec("rows_per_inch", "Rows per inch", "6.5", "rows/in"),
                            ),
                        "Body measurements" to
                            listOf(
                                InputSpec("neck_circumference", "Neck circumference", "14", "in"),
                                InputSpec("bust_circumference", "Bust circumference", "34", "in"),
                                InputSpec("ease", "Ease", "2", "in"),
                                InputSpec("underarm_width", "Underarm width", "2", "in"),
                            ),
                        "Sleeve measurements" to
                            listOf(
                                InputSpec("upper_arm_circumference", "Upper arm circumference", "12", "in"),
                                InputSpec("upper_arm_ease", "Upper arm ease", "1", "in"),
                                InputSpec("wrist_circumference", "Wrist circumference", "7.5", "in"),
                            ),
                        "Lengths" to
                            listOf(
                                InputSpec("body_length", "Body length", "13", "in"),
                                InputSpec("sleeve_length", "Sleeve length", "17", "in"),
                            ),
                        "Construction" to
                            listOf(
                                InputSpec(
                                    "increases_per_round",
                                    "Increases per round",
                                    "8",
                                    choices =
                                        listOf(
                                            "4" to "4",
                                            "8" to "8",
                                            "12" to "12",
                                            "16" to "16",
                                            "20" to "20",
                                            "24" to "24",
                                        ),
                                ),
                                InputSpec(
                                    "increase_frequency",
                                    "Increase frequency",
                                    "every_other_round",
                                    choices =
                                        listOf(
                                            "Every round" to "every_round",
                                            "Every other round" to "every_other_round",
                                        ),
                                ),
                            ),
                    ),
                stats = { s, _ ->
                    listOf(
                        "Cast on" to (num(s, "cast_on") + " sts"),
                        "Bust" to (num(s, "bust") + " sts"),
                        "Sleeve" to (num(s, "arm") + " sts"),
                        "Yoke" to (num(s, "rows") + " rnds"),
                    )
                },
            ),
            PlannerSpec(
                name = "hat",
                title = "Hat Crown Planner",
                groups =
                    listOf(
                        "Crown" to
                            listOf(
                                InputSpec("stitches", "Cast-on stitches", "80"),
                                InputSpec("repeats", "Decrease repeats", "8"),
                            ),
                    ),
                stats = { s, _ ->
                    listOf(
                        "Cast on" to (num(s, "cast_on") + " sts"),
                        "Crown" to (num(s, "rows") + " rnds"),
                    )
                },
            ),
            PlannerSpec(
                name = "sleeve",
                title = "Sleeve Decreases",
                groups =
                    listOf(
                        "Shaping" to
                            listOf(
                                InputSpec("number_of_rows", "Total rows", "61"),
                                InputSpec("starting_count", "Starting stitches", "59"),
                                InputSpec("ending_count", "Ending stitches", "43"),
                                InputSpec("decrease_per_row", "Stitches per decrease row", "2"),
                                InputSpec(
                                    "padding_mode",
                                    "Padding mode",
                                    "after",
                                    choices =
                                        listOf(
                                            "After" to "after",
                                            "Before" to "before",
                                            "Both" to "both",
                                            "None" to "none",
                                        ),
                                ),
                            ),
                    ),
                stats = { s, r ->
                    listOf(
                        "Start" to (num(s, "cast_on") + " sts"),
                        "End" to (num(r, "ending") + " sts"),
                        "Rows" to num(s, "rows"),
                    )
                },
            ),
            PlannerSpec(
                name = "sock",
                title = "Sock Calculator",
                groups =
                    listOf(
                        "Gauge" to
                            listOf(
                                InputSpec("rows_per_inch", "Rows per inch", "11", "rows/in"),
                                InputSpec("stitches_per_inch", "Stitches per inch", "9", "st/in"),
                            ),
                        "Measurements" to
                            listOf(
                                InputSpec("circumference_at_top", "Circumference at top", "10", "in"),
                                InputSpec("circumference_of_ankle", "Ankle circumference", "9.5", "in"),
                                InputSpec("length_from_sock_top_to_heel_bottom", "Top to heel", "7.75", "in"),
                                InputSpec("length_from_heel_to_toe", "Heel to toe", "10.5", "in"),
                            ),
                        "Fit" to
                            listOf(
                                InputSpec("negative_ease", "Negative ease", "20", "%"),
                            ),
                    ),
                stats = { s, r ->
                    listOf(
                        "Cast on" to (num(s, "cast_on") + " sts"),
                        "Ankle" to (num(r, "ankle_stitches") + " sts"),
                        "Rounds" to num(s, "rows"),
                    )
                },
            ),
            PlannerSpec(
                name = "yarn",
                title = "Yarn & Time Estimator",
                groups =
                    listOf(
                        "Project" to
                            listOf(
                                InputSpec(
                                    "project_type",
                                    "Project type",
                                    "hat",
                                    choices =
                                        listOf(
                                            "Hat / Beanie" to "hat",
                                            "Scarf / Cowl" to "scarf",
                                            "Triangular shawl" to "shawl_triangle",
                                            "Rectangle shawl / wrap" to "shawl_rectangle",
                                            "Crescent shawl" to "shawl_crescent",
                                            "Sweater (body only)" to "sweater",
                                            "Baby blanket" to "blanket",
                                            "Custom dimensions" to "custom",
                                        ),
                                ),
                                InputSpec("project_width", "Project width", "20", "in"),
                                InputSpec("project_height", "Project height", "9", "in"),
                            ),
                        "Gauge" to
                            listOf(
                                InputSpec("stitch_gauge", "Stitch gauge", "5", "st/in"),
                                InputSpec("row_gauge", "Row gauge", "7", "rows/in"),
                            ),
                        "Yarn" to
                            listOf(
                                InputSpec("yarn_per_ball_yards", "Yards per ball", "230", "yd"),
                                InputSpec("yarn_per_ball_grams", "Grams per ball", "50", "g"),
                            ),
                        "Pace" to
                            listOf(
                                InputSpec(
                                    "knitting_pace",
                                    "Knitting pace",
                                    "medium",
                                    choices =
                                        listOf(
                                            "Beginner / slow" to "slow",
                                            "Intermediate / average" to "medium",
                                            "Advanced / fast" to "fast",
                                        ),
                                ),
                            ),
                    ),
                stats = { s, r ->
                    listOf(
                        "Stitches" to thousands(r.opt("project_stitches")),
                        "Yarn" to (num(s, "yards") + " yd"),
                        "Weight" to (num(s, "grams") + " g"),
                        "Time" to (num(r, "hours") + " h"),
                    )
                },
            ),
        ).associateBy { it.name }

    fun forName(name: String): PlannerSpec =
        all[name]
            ?: throw IllegalArgumentException("Unknown planner: $name")
}

/**
 * The results region of a planner. Rebuilds its children for the
 * placeholder, loading, error, and success states.
 */
class ResultsPanel(
    private val activity: android.app.Activity,
    private val container: LinearLayout,
    private val onOpenSimulator: () -> Unit,
) {
    private var calculating = false

    fun showPlaceholder() {
        calculating = false
        container.removeAllViews()
        val card = activity.card()
        card.addView(
            activity.textView(
                activity.getString(org.pyknit.android.R.string.planner_results_placeholder),
                sizeSp = 14f,
                colorAttr = MR.attr.colorOnSurfaceVariant,
            ),
        )
        container.addView(card, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
    }

    fun showLoading() {
        calculating = true
        container.removeAllViews()
        container.addView(
            com.google.android.material.progressindicator.LinearProgressIndicator(activity).apply {
                isIndeterminate = true
            },
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, activity.dp(4)),
        )
    }

    fun showError(message: String) {
        calculating = false
        container.removeAllViews()
        val card = activity.card()
        card.background = activity.rounded(activity.attrColor(MR.attr.colorErrorContainer), 12)
        card.addView(
            activity.textView(
                "${activity.getString(org.pyknit.android.R.string.planner_error_prefix)}: $message",
                sizeSp = 14f,
                colorAttr = MR.attr.colorOnErrorContainer,
            ),
        )
        container.addView(card, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
    }

    fun showResult(payload: JSONObject) {
        calculating = false
        val spec = PlannerSpecs.forName(payload.getString("demo"))
        val summary = payload.getJSONObject("summary")
        val result = payload.optJSONObject("result") ?: JSONObject()
        container.removeAllViews()

        val card = activity.card()

        // Stat blocks
        val statRow = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL }
        spec.stats(summary, result).forEachIndexed { index, (label, value) ->
            statRow.addView(
                activity.statBlock(value, label),
                LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply {
                    if (index < spec.stats(summary, result).size - 1) marginEnd = activity.dp(8)
                },
            )
        }
        card.addView(statRow, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))

        // The authoritative summary line from the Python engine.
        card.addView(
            activity.textView(
                summary.optString("message"),
                sizeSp = 14f,
            ),
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(10)
            },
        )

        if (payload.has("sim_plan")) {
            card.addView(
                activity.textView(
                    activity.getString(org.pyknit.android.R.string.planner_open_simulator_hint),
                    sizeSp = 13f,
                    colorAttr = MR.attr.colorOnSurfaceVariant,
                ),
                LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                    topMargin = activity.dp(12)
                },
            )
            card.addView(
                activity.filledButton(
                    activity.getString(org.pyknit.android.R.string.planner_open_simulator),
                    onOpenSimulator,
                ),
                LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                    topMargin = activity.dp(8)
                },
            )
        }
        container.addView(card, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
    }

    fun isCalculating(): Boolean = calculating
}

/** Builds a single planner screen body (scrollable content below the app bar). */
object PlannerView {
    fun build(
        activity: android.app.Activity,
        spec: PlannerSpec,
        drafts: MutableMap<String, String>,
        calculate: (json: String, onResult: (JSONObject) -> Unit, onError: (String) -> Unit) -> Unit,
        onOpenSimulator: (valuesJson: String) -> Unit,
    ): View {
        // A field is either an EditText (raw text) or a dropdown (label -> key).
        val readers = mutableMapOf<String, () -> String>()

        fun addInput(
            column: LinearLayout,
            input: InputSpec,
        ) {
            val current = drafts[input.key] ?: input.default
            val holder: com.google.android.material.textfield.TextInputLayout
            if (input.isChoice) {
                holder = activity.choiceField(input.label, current, input.choices!!)
                val edit = holder.editText!!
                readers[input.key] = {
                    val text = edit.text?.toString().orEmpty()
                    input.choices!!.firstOrNull { it.first == text }?.second ?: text
                }
            } else {
                holder = activity.inputField(input.label, current, input.isNumeric, input.unit)
                val edit = holder.editText!!
                readers[input.key] = { edit.text?.toString().orEmpty() }
            }
            column.addView(
                holder,
                LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT,
                ).apply { bottomMargin = activity.dp(4) },
            )
        }

        val inputsColumn = activity.column()
        inputsColumn.addView(activity.screenTitle(spec.title))
        inputsColumn.addView(activity.screenIntro(activity.getString(org.pyknit.android.R.string.planner_intro)))

        spec.groups.forEach { (groupName, inputs) ->
            inputsColumn.addView(activity.sectionHeader(groupName))
            inputs.forEach { addInput(inputsColumn, it) }
        }

        val readValuesJson: () -> String = {
            val values = JSONObject()
            readers.forEach { (key, read) -> values.put(key, read()) }
            values.toString()
        }

        val resultsContainer = LinearLayout(activity).apply { orientation = LinearLayout.VERTICAL }
        val results = ResultsPanel(activity, resultsContainer) { onOpenSimulator(readValuesJson()) }
        results.showPlaceholder()

        val calculateButton = activity.filledButton(activity.getString(org.pyknit.android.R.string.planner_calculate)) { }
        calculateButton.setOnClickListener {
            if (results.isCalculating()) return@setOnClickListener
            val values = JSONObject()
            readers.forEach { (key, read) -> values.put(key, read()) }
            drafts.clear()
            drafts.putAll(values.keys().asSequence().associateWith { values.optString(it) })
            results.showLoading()
            calculateButton.text = activity.getString(org.pyknit.android.R.string.planner_calculating)
            calculateButton.isEnabled = false
            calculate(values.toString(), { payload ->
                results.showResult(payload)
                calculateButton.text = activity.getString(org.pyknit.android.R.string.planner_calculate)
                calculateButton.isEnabled = true
            }, { message ->
                results.showError(message)
                calculateButton.text = activity.getString(org.pyknit.android.R.string.planner_calculate)
                calculateButton.isEnabled = true
            })
        }
        inputsColumn.addView(
            calculateButton,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(10)
            },
        )

        val resultsColumn = activity.column()
        resultsColumn.setPadding(activity.dp(16), activity.dp(8), activity.dp(16), activity.dp(28))
        resultsColumn.addView(activity.sectionHeader(activity.getString(org.pyknit.android.R.string.planner_section_results)))
        resultsColumn.addView(
            resultsContainer,
            LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT),
        )

        val body: View =
            if (activity.isWideScreen) {
                // Tablet: inputs on the left, results pinned on the right.
                val split = LinearLayout(activity).apply { orientation = LinearLayout.HORIZONTAL }
                split.addView(inputsColumn, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
                split.addView(resultsColumn, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
                split
            } else {
                inputsColumn.addView(
                    resultsColumn,
                    LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT),
                )
                inputsColumn
            }

        return ScrollView(activity).apply {
            isFillViewport = true
            addView(activity.maxWidthFrame(body))
        }
    }
}
