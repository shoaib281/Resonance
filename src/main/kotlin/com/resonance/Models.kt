package com.resonance

import kotlinx.serialization.Serializable
import java.util.UUID

// ==========================================================================
// Enums
// ==========================================================================

enum class Goal(val value: String) {
    BRAND_AWARENESS("brand_awareness"),
    CLICKS("clicks"),
    CONTROVERSY("controversy"),
    ENGAGEMENT("engagement")
}

enum class MBTIType {
    INTJ, INTP, ENTJ, ENTP,
    INFJ, INFP, ENFJ, ENFP,
    ISTJ, ISFJ, ESTJ, ESFJ,
    ISTP, ISFP, ESTP, ESFP
}

enum class PoliticalLeaning(val value: String) {
    FAR_LEFT("far_left"),
    LEFT("left"),
    CENTER_LEFT("center_left"),
    CENTER("center"),
    CENTER_RIGHT("center_right"),
    RIGHT("right"),
    FAR_RIGHT("far_right")
}

enum class PurchasingPower(val value: String) {
    LOW("low"), MEDIUM("medium"), HIGH("high"), LUXURY("luxury")
}

enum class Mood(val value: String) {
    HAPPY("happy"), NEUTRAL("neutral"), IRRITABLE("irritable"),
    BORED("bored"), EXCITED("excited"), ANXIOUS("anxious"), CYNICAL("cynical");

    companion object {
        fun fromValue(v: String): Mood = entries.firstOrNull { it.value == v } ?: NEUTRAL
    }
}

enum class ActionType(val value: String) {
    IGNORE("ignore"),
    LIKE("like"),
    COMMENT("comment"),
    SHARE("share"),
    QUOTE_SHARE("quote_share"),
    MOCK("mock");

    companion object {
        fun fromValue(v: String): ActionType = entries.firstOrNull { it.value == v } ?: IGNORE
    }
}

// ==========================================================================
// Phase 1: Campaign Seed (the DNA the user provides)
// ==========================================================================

data class CampaignSeed(
    val content: String,
    val imageDescription: String = "",
    val goal: Goal = Goal.ENGAGEMENT,
    val targetAudience: String
)

// ==========================================================================
// Agent Profile
// ==========================================================================

data class AgentProfile(
    val id: String = UUID.randomUUID().toString().take(8),
    val name: String,
    val age: Int,
    val location: String,
    val bio: String,
    val mbti: MBTIType,
    val politicalLeaning: PoliticalLeaning,
    val purchasingPower: PurchasingPower,
    val interests: List<String>,
    var mood: Mood = Mood.NEUTRAL,
    val influenceScore: Double = 0.5,
    val following: MutableList<String> = mutableListOf(),
    val followers: MutableList<String> = mutableListOf()
)

// ==========================================================================
// Interaction record
// ==========================================================================

data class Interaction(
    val agentId: String,
    val action: ActionType,
    val content: String = "",
    val id: String = UUID.randomUUID().toString().take(8),
    val tick: Int = 0
)

// ==========================================================================
// Simulation result
// ==========================================================================

data class SimulationResult(
    val generation: Int,
    val seed: CampaignSeed,
    val interactions: MutableList<Interaction> = mutableListOf(),
    var totalReach: Int = 0,
    var likes: Int = 0,
    var comments: Int = 0,
    var shares: Int = 0,
    var mocks: Int = 0,
    var sentimentScore: Double = 0.0,
    var viralityScore: Double = 0.0,
) {
    fun computeAnalytics() {
        likes = interactions.count { it.action == ActionType.LIKE }
        comments = interactions.count { it.action in listOf(ActionType.COMMENT, ActionType.MOCK) }
        shares = interactions.count { it.action in listOf(ActionType.SHARE, ActionType.QUOTE_SHARE) }
        mocks = interactions.count { it.action == ActionType.MOCK }
        totalReach = likes + comments + shares

        val active = interactions.count { it.action != ActionType.IGNORE }
        if (active > 0) {
            sentimentScore = ((likes + shares) - mocks).toDouble() / active
            viralityScore = shares.toDouble() / active
        }
    }
}

// ==========================================================================
// JSON response models for LLM parsing
// ==========================================================================

@Serializable
data class AgentGenResponse(
    val name: String,
    val age: Int,
    val location: String,
    val bio: String,
    val mbti: String,
    val political_leaning: String,
    val purchasing_power: String,
    val interests: List<String>,
    val influence_score: Double = 0.5
)

@Serializable
data class AgentActionResponse(
    val action: String = "ignore",
    val content: String = "",
    val new_mood: String = "neutral",
    val reasoning: String = ""
)

@Serializable
data class EvolutionResponse(
    val analysis: String = "",
    val strengths: List<String> = emptyList(),
    val weaknesses: List<String> = emptyList(),
    val revised_content: String = "",
    val revised_image_description: String = "",
    val confidence: Double = 0.0
)
