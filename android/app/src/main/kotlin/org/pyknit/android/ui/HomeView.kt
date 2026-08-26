package org.pyknit.android.ui

import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.ScrollView
import com.google.android.material.R as MR
import com.google.android.material.card.MaterialCardView
import org.pyknit.android.R

/** The Tools hub: one card per tool, opened with a single tap. */
object HomeView {

    private data class Tool(val id: String, val titleRes: Int, val descRes: Int)

    private val tools = listOf(
        Tool("raglan", R.string.tool_raglan_title, R.string.tool_raglan_desc),
        Tool("hat", R.string.tool_hat_title, R.string.tool_hat_desc),
        Tool("sleeve", R.string.tool_sleeve_title, R.string.tool_sleeve_desc),
        Tool("sock", R.string.tool_sock_title, R.string.tool_sock_desc),
        Tool("sim", R.string.tool_sim_title, R.string.tool_sim_desc),
        Tool("yarn", R.string.tool_yarn_title, R.string.tool_yarn_desc),
    )

    fun build(activity: android.app.Activity, onOpen: (String) -> Unit): View {
        val c = activity.column()
        c.addView(activity.textView(
            activity.getString(R.string.tools_intro),
            sizeSp = 20f, typeface = TITLE_FACE,
        ))
        c.addView(activity.sectionHeader(activity.getString(R.string.tools_choose)))

        tools.forEach { tool ->
            val card = MaterialCardView(activity, null, MR.attr.materialCardViewStyle).apply {
                radius = activity.dp(12).toFloat()
                cardElevation = 0f
                isClickable = true
                isFocusable = true
                setCardBackgroundColor(android.content.res.ColorStateList.valueOf(activity.attrColor(MR.attr.colorSurface)))
                setStrokeColor(activity.attrColor(MR.attr.colorOutlineVariant))
                strokeWidth = activity.dp(1)
                setOnClickListener { onOpen(tool.id) }
                setContentPadding(activity.dp(16), activity.dp(14), activity.dp(16), activity.dp(14))
            }
            val inner = LinearLayout(activity).apply { orientation = LinearLayout.VERTICAL }
            inner.addView(activity.textView(activity.getString(tool.titleRes), sizeSp = 16f, typeface = TITLE_FACE))
            inner.addView(activity.textView(
                activity.getString(tool.descRes),
                sizeSp = 13.5f, colorAttr = MR.attr.colorOnSurfaceVariant,
            ))
            card.addView(inner, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
            c.addView(card, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                topMargin = activity.dp(10)
            })
        }

        return ScrollView(activity).apply {
            isFillViewport = true
            addView(activity.maxWidthFrame(c))
        }
    }
}
