package org.pyknit.android

import android.app.Activity
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.graphics.Color
import android.graphics.Typeface
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import org.json.JSONArray
import org.json.JSONObject

class MainActivity : Activity() {
    private lateinit var content: LinearLayout
    private lateinit var api: com.chaquo.python.PyObject
    private val handler = Handler(Looper.getMainLooper())
    private var simulation: JSONObject? = null
    private var simulationIndex = 0
    private var playing = false
    private var instructionsField: EditText? = null
    private var simulationStatus: TextView? = null
    private var simulationPicture: TextView? = null
    private var canonicalPlan = ""
    private var plannerInputs = mutableMapOf<String, EditText>()

    private val purple = Color.rgb(109, 76, 141)
    private val ink = Color.rgb(44, 38, 50)
    private val paper = Color.rgb(250, 247, 252)

    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        if (!Python.isStarted()) Python.start(AndroidPlatform(this))
        api = Python.getInstance().getModule("pyknit.chaquopy.mobile_api")
        showHome()
    }

    private fun text(value: String, size: Float = 16f, bold: Boolean = false): TextView =
        TextView(this).apply {
            this.text = value
            textSize = size
            setTextColor(ink)
            setPadding(16, 10, 16, 10)
            if (bold) typeface = Typeface.DEFAULT_BOLD
        }

    private fun button(label: String, action: () -> Unit): Button = Button(this).apply {
        this.text = label
        setOnClickListener { action() }
        isAllCaps = false
    }

    private fun column(): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(16, 12, 16, 24)
    }

    private fun setScreen(view: View) {
        val frame = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(paper)
        }
        frame.addView(text("pyKnit · offline knitting tools", 18f, true))
        val navScroll = HorizontalScrollView(this)
        val nav = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        listOf(
            "Home" to { showHome() },
            "Raglan" to { showPlanner("raglan") },
            "Hat" to { showPlanner("hat") },
            "Sleeve" to { showPlanner("sleeve") },
            "Sock" to { showPlanner("sock") },
            "Simulator" to { showSimulator() },
            "Yarn" to { showPlanner("yarn") },
        ).forEach { (label, action) -> nav.addView(button(label, action)) }
        navScroll.addView(nav)
        frame.addView(navScroll, LinearLayout.LayoutParams(-1, -2))
        val scroll = ScrollView(this)
        content = column()
        content.addView(view)
        scroll.addView(content)
        frame.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        setContentView(frame)
    }

    private fun showHome() {
        val c = column()
        c.addView(text("Knit from the numbers, not from a mystery box.", 26f, true))
        c.addView(text("The Android app embeds the existing pyKnit Python calculations. It works offline after installation; Kotlin is only the native shell."))
        c.addView(text("Choose a tool", 20f, true))
        listOf(
            "Raglan Sweater Planner" to "Gauge and measurements → exact top-down sweater pattern",
            "Hat Crown Planner" to "A decrease schedule with a practical crown shape",
            "Sleeve Decreases" to "Check even decrease spacing and final stitches",
            "Sock Calculator" to "Calculate a complete top-down sock plan",
            "Knit Simulator" to "Step through manual or planner-generated instructions",
            "Yarn & Time Estimator" to "Estimate yarn, weight, and knitting time",
        ).forEach { (name, description) ->
            c.addView(button(name) {
                val key = when (name) {
                    "Raglan Sweater Planner" -> "raglan"
                    "Hat Crown Planner" -> "hat"
                    "Sleeve Decreases" -> "sleeve"
                    "Sock Calculator" -> "sock"
                    "Knit Simulator" -> "sim"
                    else -> "yarn"
                }
                if (key == "sim") showSimulator() else showPlanner(key)
            })
            c.addView(text(description, 14f))
        }
        setScreen(c)
    }

    private fun input(c: LinearLayout, key: String, label: String, value: String) {
        c.addView(text(label, 14f, true))
        val field = EditText(this).apply {
            setText(value)
            hint = label
            setSingleLine(true)
        }
        c.addView(field, LinearLayout.LayoutParams(-1, -2))
        plannerInputs[key] = field
    }

    private fun showPlanner(name: String) {
        plannerInputs.clear()
        val c = column()
        val title = when (name) {
            "raglan" -> "Raglan Sweater Planner"
            "hat" -> "Hat Crown Planner"
            "sleeve" -> "Sleeve Decreases"
            "sock" -> "Sock Calculator"
            else -> "Yarn & Time Estimator"
        }
        c.addView(text(title, 25f, true))
        c.addView(text("These fields are sent to the existing Python demo module. No calculation is duplicated in Kotlin."))
        when (name) {
            "raglan" -> {
                val d = mapOf(
                    "stitches_per_inch" to "5", "rows_per_inch" to "6.5",
                    "neck_circumference" to "14", "bust_circumference" to "34",
                    "ease" to "2", "underarm_width" to "2",
                    "upper_arm_circumference" to "12", "upper_arm_ease" to "1",
                    "wrist_circumference" to "7.5", "body_length" to "13",
                    "sleeve_length" to "17", "increases_per_round" to "8",
                    "increase_frequency" to "every_other_round"
                )
                d.forEach { (key, value) -> input(c, key, key.replace('_', ' '), value) }
            }
            "hat" -> { input(c, "stitches", "cast-on stitches", "80"); input(c, "repeats", "decrease repeats", "8") }
            "sleeve" -> {
                input(c, "number_of_rows", "total rows", "61"); input(c, "starting_count", "starting stitches", "59")
                input(c, "ending_count", "ending stitches", "43"); input(c, "decrease_per_row", "stitches per decrease row", "2")
                input(c, "padding_mode", "padding mode (after/before/both/none)", "after")
            }
            "sock" -> {
                val d = mapOf("rows_per_inch" to "11", "stitches_per_inch" to "9", "circumference_at_top" to "10", "circumference_of_ankle" to "9.5", "length_from_sock_top_to_heel_bottom" to "7.75", "length_from_heel_to_toe" to "10.5", "negative_ease" to "20")
                d.forEach { (key, value) -> input(c, key, key.replace('_', ' '), value) }
            }
            else -> {
                val d = mapOf("project_type" to "hat", "project_width" to "20", "project_height" to "8", "stitch_gauge" to "5", "row_gauge" to "7", "yarn_per_ball_yards" to "220", "yarn_per_ball_grams" to "100", "knitting_pace" to "medium")
                d.forEach { (key, value) -> input(c, key, key.replace('_', ' '), value) }
            }
        }
        val resultText = text("Run the calculation to see the authoritative Python result.")
        c.addView(button("Calculate") {
            try {
                val result = callPlanner(name)
                resultText.text = summaryText(result.getJSONObject("summary"))
                if (result.has("sim_plan")) {
                    c.addView(button("Open exact pattern in Knit Simulator") {
                        openPlannerSimulator(name)
                    }, 0)
                }
            } catch (e: Exception) { resultText.text = "Could not calculate: ${cleanError(e)}" }
        })
        c.addView(resultText)
        setScreen(c)
    }

    private fun valuesJson(): String {
        val o = JSONObject()
        plannerInputs.forEach { (key, field) -> o.put(key, field.text.toString()) }
        return o.toString()
    }

    private fun callPlanner(name: String): JSONObject = JSONObject(
        api.callAttr("planner_result", name, valuesJson()).toJava(String::class.java)
    )

    private fun summaryText(summary: JSONObject): String {
        val lines = mutableListOf(summary.optString("title"), summary.optString("message"))
        if (summary.has("sections")) lines.add("Phases: " + summary.getJSONArray("sections").join(" · ").replace("\"", ""))
        return lines.joinToString("\n")
    }

    private fun openPlannerSimulator(name: String) {
        try {
            val result = JSONObject(api.callAttr("planner_to_simulator", name, valuesJson()).toJava(String::class.java))
            canonicalPlan = result.getJSONObject("sim_plan").toString()
            showSimulator(result.getString("instructions"), canonicalPlan, result.getJSONObject("simulation"))
        } catch (e: Exception) { toast("Could not open simulator: ${cleanError(e)}") }
    }

    private fun showSimulator(prefill: String = "co 10\nk2 p2 across\nk2 p2 across\nk all", plan: String = "", ready: JSONObject? = null) {
        playing = false
        canonicalPlan = plan
        val c = column()
        c.addView(text("Knit Simulator", 25f, true))
        c.addView(text("The field below is the source of truth. Planner patterns are copied exactly; editing the field switches to an independent manual simulation."))
        val field = EditText(this).apply {
            setText(prefill)
            minLines = 8
            gravity = Gravity.TOP
            setTextIsSelectable(true)
        }
        instructionsField = field
        c.addView(field, LinearLayout.LayoutParams(-1, 260))
        val controls = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        controls.addView(button("Build") { build(field.text.toString()) })
        controls.addView(button("Previous") { move(-1) })
        controls.addView(button("Next") { move(1) })
        controls.addView(button(if (playing) "Pause" else "Play") { togglePlay(field) })
        controls.addView(button("Reset") { reset() })
        c.addView(HorizontalScrollView(this).apply { addView(controls) })
        val status = text("Build Simulation to validate and step through the instructions.")
        val picture = text("", 18f)
        simulationStatus = status
        simulationPicture = picture
        c.addView(status)
        c.addView(picture)
        if (ready != null) {
            simulation = ready
            simulationIndex = 0
            renderSimulation(status, picture)
        }
        setScreen(c)
    }

    private fun build(instructions: String) {
        try {
            val plan = if (canonicalPlan.isNotEmpty()) canonicalPlan else ""
            val wrapper = JSONObject(api.callAttr("build_simulation", instructions, plan).toJava(String::class.java))
            simulation = wrapper.getJSONObject("simulation")
            simulationIndex = 0
            renderCurrent()
        } catch (e: Exception) { toast("Simulation error: ${cleanError(e)}") }
    }

    private fun renderCurrent() {
        val status = simulationStatus ?: return
        val picture = simulationPicture ?: return
        renderSimulation(status, picture)
    }

    private fun renderSimulation(status: TextView, picture: TextView) {
        val sim = simulation ?: return
        val steps = sim.getJSONArray("steps")
        if (steps.length() == 0) return
        simulationIndex = simulationIndex.coerceIn(0, steps.length() - 1)
        val step = steps.getJSONObject(simulationIndex)
        val section = step.optString("section_label", if (sim.optString("garment") == "sweater") "Manual pattern" else sim.optString("garment"))
        val row = step.optInt("row", 0)
        val n = step.optInt("n", 0)
        val before = step.optInt("before", 0)
        val op = step.optString("op", "")
        val transition = if (before > 0 && before != n) " · $before → $n stitches" else " · $n stitches"
        status.text = "Step ${simulationIndex + 1} / ${steps.length()}\n$section · Row $row$transition\nNext: $op"
        picture.text = if (sim.optString("garment") == "sweater" || sim.optString("garment") == "raglan") garmentSketch(step) else swatchSketch(steps, simulationIndex, step)
    }

    private fun garmentSketch(step: JSONObject): String {
        val label = step.optString("section_label", "Sweater")
        val width = (step.optInt("n", 0) / 12).coerceIn(3, 18)
        val sleeve = "=".repeat((width / 2).coerceAtLeast(2))
        return """        .-''''-.
       /  neck  \\
  $sleeve/  $label  \\$sleeve
     /            \\
    |    BODY      |
    |              |
    |______________|

Actual current needle count: ${step.optInt("n", 0)} stitches"""
    }

    private fun swatchSketch(steps: JSONArray, index: Int, step: JSONObject): String {
        val loops = "○ ".repeat(step.optInt("n", 0).coerceAtMost(40))
        val rows = StringBuilder("Needle: $loops\n\nCompleted fabric:\n")
        for (i in 1..index) {
            val row = steps.getJSONObject(i)
            val ops = row.optJSONArray("row_ops")
            val glyph = StringBuilder()
            if (ops != null) for (j in 0 until ops.length()) glyph.append(if (ops.optInt(j) == 1) "∩ " else "∨ ")
            rows.append("Row ${row.optInt("row")}: $glyph\n")
        }
        return rows.toString()
    }

    private fun move(delta: Int) {
        val sim = simulation ?: return
        simulationIndex = (simulationIndex + delta).coerceIn(0, sim.getJSONArray("steps").length() - 1)
        renderCurrent()
    }

    private fun reset() { playing = false; simulationIndex = 0; renderCurrent() }

    private fun togglePlay(field: EditText) {
        if (simulation == null) { build(field.text.toString()); return }
        playing = !playing
        if (playing) playNext(field)
    }

    private fun playNext(field: EditText) {
        if (!playing) return
        val sim = simulation ?: return
        if (simulationIndex >= sim.getJSONArray("steps").length() - 1) { playing = false; return }
        simulationIndex++
        renderCurrent()
        handler.postDelayed({ playNext(field) }, sim.optInt("speed_ms", 400).toLong())
    }

    private fun cleanError(e: Exception): String = e.message?.substringAfterLast(": ") ?: "unknown error"
    private fun toast(message: String) = Toast.makeText(this, message, Toast.LENGTH_LONG).show()
}
