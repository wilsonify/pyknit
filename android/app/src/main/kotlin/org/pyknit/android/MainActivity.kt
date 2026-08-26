package org.pyknit.android

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Menu
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.google.android.material.R as MR
import org.json.JSONObject
import org.pyknit.android.ui.HomeView
import org.pyknit.android.ui.PlannerSpecs
import org.pyknit.android.ui.PlannerView
import org.pyknit.android.ui.SimulatorView
import org.pyknit.android.ui.attrColor
import org.pyknit.android.ui.hairline

/**
 * Native shell around the existing pyKnit Python calculations.
 *
 * Python remains the source of truth for all knitting math; this activity
 * only navigates and presents. Planner and simulator results are produced
 * by `pyknit/chaquopy/mobile_api.py` and rendered here.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var api: PyObject
    private val handler = Handler(Looper.getMainLooper())

    private lateinit var toolbar: MaterialToolbar
    private lateinit var contentHost: FrameLayout
    private lateinit var bottomNav: BottomNavigationView

    private enum class Screen { TOOLS, PLANNER, SIMULATOR }
    private var currentScreen = Screen.TOOLS
    private var simulatorFromPlanner = false

    private val plannerDrafts = mutableMapOf<String, MutableMap<String, String>>()

    // Simulator state, owned here so it survives tab switches.
    var simulation: JSONObject? = null
    var simulationIndex = 0
    var playing = false
    var canonicalPlan = ""
    var draftInstructions = "co 10\nk2 p2 across\nk2 p2 across\nk all"

    private val simulatorView = SimulatorView(this)

    private companion object {
        const val ID_TOOLS = 1
        const val ID_SIMULATOR = 2
    }

    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        if (!Python.isStarted()) Python.start(AndroidPlatform(this))
        api = Python.getInstance().getModule("pyknit.chaquopy.mobile_api")
        buildShell()
        showTools()
    }

    // ---------- shell ----------

    private fun buildShell() {
        val frame = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }

        toolbar = MaterialToolbar(this).apply {
            setTitleTextColor(attrColor(MR.attr.colorOnSurface))
            setBackgroundColor(attrColor(MR.attr.colorSurface))
            setNavigationIcon(androidx.appcompat.R.drawable.abc_ic_ab_back_material)
            setNavigationContentDescription(getString(R.string.back))
            setNavigationOnClickListener { onBackPressed() }
            navigationIcon = null
        }
        frame.addView(toolbar, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))

        val divider = hairline()
        frame.addView(divider, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 1))

        contentHost = FrameLayout(this)
        frame.addView(contentHost, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))

        bottomNav = BottomNavigationView(this, null, MR.attr.bottomNavigationStyle).apply {
            setBackgroundColor(attrColor(MR.attr.colorSurface))
            labelVisibilityMode = BottomNavigationView.LABEL_VISIBILITY_LABELED
            menu.add(Menu.NONE, ID_TOOLS, 0, getString(R.string.nav_tools)).setIcon(R.drawable.ic_tools)
            menu.add(Menu.NONE, ID_SIMULATOR, 1, getString(R.string.nav_simulator)).setIcon(R.drawable.ic_simulator)
            setOnItemSelectedListener { item ->
                when (item.itemId) {
                    ID_TOOLS -> { if (currentScreen != Screen.TOOLS) showTools(); true }
                    ID_SIMULATOR -> { if (currentScreen != Screen.SIMULATOR) showSimulator(); true }
                    else -> false
                }
            }
        }
        frame.addView(bottomNav, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))

        setContentView(frame)
    }

    private fun setScreen(title: String, back: Boolean, body: View) {
        toolbar.title = title
        toolbar.navigationIcon = if (back) {
            androidx.appcompat.content.res.AppCompatResources.getDrawable(this, androidx.appcompat.R.drawable.abc_ic_ab_back_material)
        } else {
            null
        }
        contentHost.removeAllViews()
        contentHost.addView(body, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
    }

    override fun onBackPressed() {
        when (currentScreen) {
            Screen.PLANNER -> showTools()
            Screen.SIMULATOR -> if (simulatorFromPlanner) showTools() else super.onBackPressed()
            Screen.TOOLS -> super.onBackPressed()
        }
    }

    // ---------- screens ----------

    private fun showTools() {
        playing = false
        currentScreen = Screen.TOOLS
        setScreen(getString(R.string.tools_title), back = false, body = HomeView.build(this) { openTool(it) })
        selectNav(ID_TOOLS)
    }

    private fun openTool(id: String) {
        if (id == "sim") showSimulator() else showPlanner(id)
    }

    private fun showPlanner(name: String) {
        playing = false
        currentScreen = Screen.PLANNER
        val spec = PlannerSpecs.forName(name)
        val drafts = plannerDrafts.getOrPut(name) { mutableMapOf() }
        val body = PlannerView.build(
            activity = this,
            spec = spec,
            drafts = drafts,
            calculate = { json, onResult, onError -> callPlanner(name, json, onResult, onError) },
            onOpenSimulator = { valuesJson -> openPlannerSimulator(name, valuesJson) },
        )
        setScreen(spec.title, back = true, body)
        selectNav(ID_TOOLS)
    }

    private fun showSimulator() {
        simulatorFromPlanner = false
        currentScreen = Screen.SIMULATOR
        setScreen(getString(R.string.sim_title), back = false, body = simulatorView.build())
        selectNav(ID_SIMULATOR)
    }

    /** Select a bottom-nav item without re-triggering the selection listener. */
    private fun selectNav(itemId: Int) {
        if (bottomNav.selectedItemId != itemId) bottomNav.selectedItemId = itemId
    }

    // ---------- Python bridge ----------

    private fun callPlanner(
        name: String,
        json: String,
        onResult: (JSONObject) -> Unit,
        onError: (String) -> Unit,
    ) {
        Thread {
            try {
                val result = JSONObject(
                    api.callAttr("planner_result", name, json).toJava(String::class.java)
                )
                handler.post { onResult(result) }
            } catch (e: Exception) {
                handler.post { onError(cleanError(e)) }
            }
        }.start()
    }

    private fun openPlannerSimulator(name: String, valuesJson: String) {
        Thread {
            try {
                val result = JSONObject(
                    api.callAttr("planner_to_simulator", name, valuesJson).toJava(String::class.java)
                )
                handler.post {
                    canonicalPlan = result.getJSONObject("sim_plan").toString()
                    draftInstructions = result.getString("instructions")
                    simulation = result.getJSONObject("simulation")
                    simulationIndex = 0
                    playing = false
                    simulatorFromPlanner = true
                    showSimulator()
                    simulatorView.bringStatusIntoView()
                }
            } catch (e: Exception) {
                handler.post { toast("Could not open simulator: ${cleanError(e)}") }
            }
        }.start()
    }

    fun buildSimulation(instructions: String) {
        Thread {
            try {
                val wrapper = JSONObject(
                    api.callAttr("build_simulation", instructions, canonicalPlan).toJava(String::class.java)
                )
                handler.post {
                    simulation = wrapper.getJSONObject("simulation")
                    simulationIndex = 0
                    playing = false
                    simulatorView.refresh()
                    simulatorView.bringStatusIntoView()
                }
            } catch (e: Exception) {
                handler.post { simulatorView.showError(cleanError(e)) }
            }
        }.start()
    }

    // ---------- simulator controls ----------

    fun move(delta: Int) {
        val sim = simulation ?: return
        playing = false
        simulationIndex = (simulationIndex + delta).coerceIn(0, sim.getJSONArray("steps").length() - 1)
        simulatorView.refresh()
    }

    fun moveTo(index: Int) {
        val sim = simulation ?: return
        playing = false
        simulationIndex = index.coerceIn(0, sim.getJSONArray("steps").length() - 1)
        simulatorView.refresh()
    }

    fun resetSimulation() = moveTo(0)

    fun togglePlay() {
        if (simulation == null) {
            buildSimulation(draftInstructions)
            return
        }
        playing = !playing
        simulatorView.refresh()
        if (playing) schedulePlay()
    }

    private fun schedulePlay() {
        if (!playing) return
        val sim = simulation ?: return
        val total = sim.getJSONArray("steps").length()
        if (simulationIndex >= total - 1) {
            playing = false
            simulatorView.refresh()
            return
        }
        val speed = sim.optInt("speed_ms", 400)
        handler.postDelayed({
            if (!playing) return@postDelayed
            simulationIndex++
            simulatorView.refresh()
            schedulePlay()
        }, speed.toLong())
    }

    // ---------- helpers ----------

    private fun cleanError(e: Exception): String =
        e.message?.substringAfterLast(": ") ?: "unknown error"

    private fun toast(message: String) = Toast.makeText(this, message, Toast.LENGTH_LONG).show()
}
