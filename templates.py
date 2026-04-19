"""Template engine for generating stakeholder perspectives without an LLM."""

import json
import random
import re
import time
from pathlib import Path

SCENARIOS_DIR = Path(__file__).parent / "scenarios"

# === Persona Archetypes ===

ARCHETYPES = {
    "pm": {
        "concerns": [
            "This changes the roadmap calculus. {detail} means we need to re-evaluate what we committed to for {timeframe}.",
            "The question isn't whether this matters. It's what we're willing to trade. Every yes here is a no somewhere else.",
            "I need to separate the signal from the noise. {detail} sounds urgent, but is it strategically important or just loud?",
            "If we react to this without a framework, we set a precedent. Next time someone raises {topic}, they'll expect the same response.",
        ],
        "strategies": [
            "Frame this as a data-driven decision. Gather evidence before committing resources.",
            "Propose a time-boxed investigation before making a permanent roadmap change.",
            "Quantify the trade-off: what does saying yes cost in terms of other commitments?",
            "Build alignment across stakeholders before announcing a direction.",
        ],
        "dialogue_openers": [
            "Let me frame what I think we're actually deciding here.",
            "Before we jump to solutions, I want to make sure we agree on the problem.",
            "I've been thinking about this, and I think there's a framing that helps.",
            "Let's separate the urgent from the important for a second.",
        ],
        "dialogue_thoughts": [
            "Need to keep this structured or it'll devolve into whoever argues loudest.",
            "If I can get alignment on the criteria first, the decision almost makes itself.",
            "Careful not to look indecisive. Pick a direction and own it, even if it's 'we need more data.'",
        ],
        "tags": ["Strategy", "Key Question", "Priority"],
        "vocab": ["roadmap", "trade-off", "scope", "prioritize", "align", "ship"],
    },
    "eng": {
        "concerns": [
            "The technical reality is more complex than the meeting room version. {detail} touches at least three systems.",
            "We can build this fast or build this right. Fast means we revisit it in two quarters with twice the cost.",
            "I'm worried about the hidden dependencies. {detail} sounds straightforward until you look at what it actually touches.",
            "The 'quick fix' path creates technical debt that compounds. Every shortcut we take now makes the next feature harder.",
        ],
        "strategies": [
            "Propose the minimal viable architecture that doesn't create throwaway work.",
            "Offer a phased approach: foundation now, full feature next quarter.",
            "Quantify the tech debt cost of the fast path vs. doing it properly.",
            "Identify what can be reused from existing systems before building new.",
        ],
        "dialogue_openers": [
            "Let me give you the engineering reality check on this.",
            "There are two ways to build this, and the difference matters.",
            "From a technical standpoint, here's what I think people are underestimating.",
            "I want to make sure we're not confusing 'simple to describe' with 'simple to build.'",
        ],
        "dialogue_thoughts": [
            "If I don't push back on the timeline now, we'll own the fallout when it slips.",
            "The right architecture pays for itself in 6 months. But nobody wants to hear '6 months' right now.",
            "I need to frame this as risk management, not engineering perfectionism.",
        ],
        "tags": ["Technical Reality", "Concern", "Risk Assessment"],
        "vocab": ["architecture", "sprint", "refactor", "scalable", "debt", "ship"],
    },
    "sales": {
        "concerns": [
            "This hits the pipeline directly. {detail} affects at least three active deals I'm tracking.",
            "Customers don't wait for our internal debates. While we're discussing, competitors are demoing.",
            "The market reads our actions, not our intentions. {detail} sends a signal whether we want it to or not.",
            "I need something concrete to put in front of customers. Roadmap slides don't close deals.",
        ],
        "strategies": [
            "Get a committed date or deliverable that can be shared externally.",
            "Frame any delay as a strategic choice, not a failure. Customers respect honesty.",
            "Identify which specific deals are affected and quantify the pipeline risk.",
            "Arm the champion with internal ammunition to keep the deal alive.",
        ],
        "dialogue_openers": [
            "Let me put real numbers on what we're talking about here.",
            "I want to make sure the customer perspective is on the table.",
            "From the field, here's what I'm hearing that might change the calculus.",
            "I have three deals where this is coming up in active conversations.",
        ],
        "dialogue_thoughts": [
            "Put customer names and dollar amounts on the table. Abstract discussions get abstract answers.",
            "Don't let them frame this as 'Sales panicking.' This is market signal.",
            "If I push too hard I look self-interested. Frame it as customer voice, not quota pressure.",
        ],
        "tags": ["Impact", "Risk Assessment", "Urgency"],
        "vocab": ["pipeline", "deal", "competitive", "revenue", "close", "champion"],
    },
    "cs": {
        "concerns": [
            "My top accounts are affected. {detail} changes what I promised them in our last QBR.",
            "Trust takes months to build and one conversation to break. How we handle {topic} defines the relationship.",
            "The customer's planning cycle doesn't align with ours. They've already committed internally based on what we told them.",
            "Churn doesn't happen in one moment. It's a slow erosion of confidence. {detail} is another chip.",
        ],
        "strategies": [
            "Proactive communication to affected accounts before they hear from competitors.",
            "Offer a concrete alternative or workaround for the transition period.",
            "Identify which accounts are at actual risk vs. inconvenienced.",
            "Turn this into a trust-building moment by being transparent about the trade-off.",
        ],
        "dialogue_openers": [
            "I need to flag the customer impact here because it's real and it's immediate.",
            "Let me share what I'm hearing from accounts that changes this picture.",
            "Before we finalize, I want to make sure we have a story for affected customers.",
            "The accounts I'm most worried about are the ones who've already planned around this.",
        ],
        "dialogue_thoughts": [
            "If I don't advocate for the customer, nobody will. That's literally my job.",
            "Need to separate actual churn risk from inconvenience. Not every account is at the same risk level.",
            "Proposing a middle ground is stronger than just saying 'customers will be upset.'",
        ],
        "tags": ["Urgency", "Mitigation", "Impact"],
        "vocab": ["churn", "adoption", "trust", "retention", "QBR", "escalation"],
    },
    "design": {
        "concerns": [
            "We're making assumptions about users that haven't been validated. {detail} sounds logical but we don't have evidence.",
            "The user experience debt is piling up. {detail} adds another layer of complexity that users have to navigate.",
            "I keep hearing what stakeholders want. I haven't heard what users need. Those aren't always the same thing.",
            "If we ship {topic} without research, we're optimizing for our org chart, not for the person using the product.",
        ],
        "strategies": [
            "Run a fast discovery sprint (2-3 days) before committing to a direction.",
            "Map the actual user journey to find where the real friction is.",
            "Prototype and test cheaply before building the full solution.",
            "Challenge the stated requirement. The first request is rarely the real need.",
        ],
        "dialogue_openers": [
            "Can I push back on something? I don't think we've talked to users about this yet.",
            "There's a UX angle here that I think we're missing.",
            "Before we commit to building, can we validate that this is actually the right solution?",
            "I want to flag that the stated requirement and the actual user need might be different.",
        ],
        "dialogue_thoughts": [
            "Everyone wants to jump to building. Two days of research would save two months of building the wrong thing.",
            "I sound like I'm slowing things down, but shipping the wrong solution is slower than validating first.",
            "If I can get them to agree to a quick test, the data will make the argument for me.",
        ],
        "tags": ["Blind Spot", "Concern", "Key Question"],
        "vocab": ["user flow", "friction", "accessibility", "prototype", "validate", "journey"],
    },
    "uxr": {
        "concerns": [
            "We don't have data to support this direction. {detail} is based on stakeholder intuition, not user evidence.",
            "The sample we're drawing conclusions from is too small. Three conversations isn't a pattern.",
            "There's a selection bias in what we're hearing. The loudest customers aren't representative of the base.",
            "We're confusing 'customers asked for X' with 'customers need X.' The stated preference often masks the real need.",
        ],
        "strategies": [
            "Design a lightweight study that can answer the key question in under a week.",
            "Triangulate: combine behavioral data, qualitative interviews, and support tickets.",
            "Challenge assumptions by reframing the question. Ask 'why' before asking 'what.'",
            "Segment the findings. What's true for enterprise might not be true for mid-market.",
        ],
        "dialogue_openers": [
            "I want to flag an evidence gap before we commit to a direction.",
            "The data we have tells a different story than what I'm hearing in this room.",
            "Can I share what we've actually observed in research? It might reframe this.",
            "Before we build on this assumption, let me tell you what the research shows.",
        ],
        "dialogue_thoughts": [
            "Nobody wants to hear 'we need more research' when there's urgency. Frame it as risk reduction, not delay.",
            "The data I have isn't perfect, but it's better than the anecdotes driving this decision.",
            "If I can get one concrete number into this discussion, it'll anchor the conversation in reality.",
        ],
        "tags": ["Blind Spot", "Key Question", "Risk Assessment"],
        "vocab": ["signal", "sample", "bias", "validate", "segment", "behavioral"],
    },
    "sc": {
        "concerns": [
            "I'm the one who has to make this work in the customer's environment. {detail} sounds clean in theory but deployment is messy.",
            "Every customer's infrastructure is different. What works for one might break for another.",
            "The gap between the demo and reality is where deals die. {detail} widens that gap.",
            "I need to tell customers the truth about what this can and can't do. Overselling creates implementation nightmares.",
        ],
        "strategies": [
            "Map the implementation path for the top 3 customer environments before committing.",
            "Identify configuration vs. customization boundaries upfront.",
            "Build a POC that proves feasibility in the customer's actual stack.",
            "Document what's supported vs. what's theoretically possible.",
        ],
        "dialogue_openers": [
            "Let me bring the implementation lens to this. The field sees things differently.",
            "I've done this deployment at four customers. Here's what actually happens.",
            "The demo version and the production version of this are very different conversations.",
            "From a customer deployment perspective, here's what concerns me.",
        ],
        "dialogue_thoughts": [
            "I'm the bridge between what we promise and what we deliver. If I stay quiet now, I'll own the fallout later.",
            "Sales wants me to say it's easy. Engineering wants me to say it's complex. The truth is in between.",
            "If I can propose a POC, it buys everyone time and gives us real data.",
        ],
        "tags": ["Technical Reality", "Mitigation", "Concern"],
        "vocab": ["deployment", "configuration", "integration", "POC", "environment", "feasibility"],
    },
    "exec": {
        "concerns": [
            "I need to see the strategic picture, not just the tactical one. {detail} matters, but how does it fit the 12-month plan?",
            "Every resource decision is a portfolio decision. What are we NOT doing if we do this?",
            "The market window is real. Being 80% right and on time beats 100% right and late.",
            "I need my team aligned on a direction, even if it's imperfect. Indecision is more expensive than a wrong call we can correct.",
        ],
        "strategies": [
            "Set a decision deadline. Gather what data you can by then and make the call.",
            "Define the reversibility: if this is wrong, how hard is it to change course?",
            "Assign clear ownership: one person makes the call, others provide input.",
            "Align the decision to a measurable outcome we can evaluate in 90 days.",
        ],
        "dialogue_openers": [
            "Let me step back and frame what I think the actual decision is here.",
            "I've been listening, and I think we're conflating two separate questions.",
            "Here's what I need to see to make a call on this.",
            "I want to be clear about the decision framework so we're not relitigating this in two weeks.",
        ],
        "dialogue_thoughts": [
            "I need to make a call that sticks. If I waffle, the team will read it as indecision and hedge their bets.",
            "The right move is probably obvious to me, but I need the team to arrive there together or they won't execute.",
            "Threading the needle: validate the person who raised this without committing to their preferred solution.",
        ],
        "tags": ["Decision Framework", "Priority", "Strategy"],
        "vocab": ["portfolio", "market window", "ROI", "strategic", "bet", "alignment"],
    },
}

# Default persona definitions
DEFAULT_PERSONAS = {
    "pm": {"name": "Product Manager", "role": "Release Owner", "color": "#4338ca", "avatar": "PM"},
    "eng": {"name": "Engineering Lead", "role": "Platform Team", "color": "#b91c1c", "avatar": "EL"},
    "sales": {"name": "Sales", "role": "Enterprise Account Executive", "color": "#047857", "avatar": "SA"},
    "cs": {"name": "Customer Success", "role": "Strategic Accounts Manager", "color": "#b45309", "avatar": "CS"},
    "design": {"name": "Design", "role": "Product Designer", "color": "#7e22ce", "avatar": "DS"},
    "uxr": {"name": "User Researcher", "role": "Research Lead", "color": "#be185d", "avatar": "UR"},
    "sc": {"name": "Solution Consultant", "role": "Pre-Sales Technical", "color": "#475569", "avatar": "SC"},
    "exec": {"name": "Executive Sponsor", "role": "VP of Product", "color": "#0369a1", "avatar": "VP"},
}


# === Context-specific concern and strategy variants ===

CONTEXT_CONCERNS = {
    "pm": {
        "b2b": [
            "In a B2B product, {detail} affects renewal conversations and expansion revenue, not just acquisition. Our CS team will feel it first.",
            "Enterprise buyers evaluate us on roadmap predictability. {detail} changes what we can credibly promise in {timeframe}.",
        ],
        "b2c": [
            "At consumer scale, {detail} isn't one conversation — it's thousands of silent churns and one-star reviews.",
            "B2C users have no support contract. {detail} either earns trust in the product or loses it silently.",
        ],
        "startup": [
            "At our stage, {detail} isn't just a product decision — it defines our category positioning before the market has made up its mind.",
            "We don't have the brand equity to recover from a wrong call here. {detail} needs to be right, not just shipped.",
        ],
        "enterprise_co": [
            "At our size, {detail} requires alignment across multiple teams before it ships. Getting the framing right upfront is faster than fixing it later.",
            "Our enterprise customer base has budget cycles and contractual commitments. {detail} triggers obligations we need to plan around.",
        ],
        "urgent": [
            "We don't have time for a perfect framework. I need the minimum viable alignment to make a defensible call today.",
            "Fast decisions need clear criteria. What would we need to see to feel confident either way — and do we have that data right now?",
        ],
    },
    "eng": {
        "b2b": [
            "Enterprise customers have unique environments. {detail} needs to survive their security reviews, SSO requirements, and audit trails.",
            "Our largest accounts are on custom infrastructure. {detail} can't be a one-size-fits-all solution.",
        ],
        "b2c": [
            "At consumer scale, {detail} means we're touching millions of sessions. A 2% performance regression is a user complaint surge.",
            "B2C traffic is unpredictable. Whatever we ship for {detail} needs to hold under 10x expected load.",
        ],
        "startup": [
            "We're still in the 'move fast and learn' phase, but {detail} is the kind of debt that becomes unfixable after we scale.",
            "Small team means every architectural decision is load-bearing. {detail} touches the foundations, not just the surface.",
        ],
        "enterprise_co": [
            "At our engineering scale, {detail} goes through security review, compliance sign-off, and multiple team dependencies before it ships.",
            "Coordinating across platform, product, and infra for {detail} adds weeks. That's not pessimism — that's our actual process.",
        ],
        "urgent": [
            "I can ship something today, but I want everyone to understand what we're trading. The fast path means we revisit this in 60 days.",
            "There's a version of this that ships quickly if we accept the constraints. Let me walk you through what those constraints actually are.",
        ],
    },
    "sales": {
        "b2b": [
            "In enterprise sales, {detail} affects multi-stakeholder buying committees. One champion's concern kills the deal if we don't get ahead of it.",
            "My top prospects are mid-evaluation. {detail} changes what I can honestly say about our roadmap in active conversations.",
        ],
        "b2c": [
            "Consumer decisions are fast and emotional. {detail} will hit social sentiment before our PR team has a draft response ready.",
            "In B2C, we don't get a second chance at first impression. {detail} affects trial conversion for everyone in the funnel right now.",
        ],
        "startup": [
            "We're still proving product-market fit. {detail} affects whether prospects see us as a credible long-term bet or a risk they can't justify.",
            "Every logo matters at our stage. {detail} is the kind of thing that makes a cautious buyer pause.",
        ],
        "enterprise_co": [
            "At our deal sizes, {detail} is a renegotiation trigger. Legal will want to revisit contract terms if we change what we promised.",
            "Our enterprise accounts have executive sponsors who track product commitments. {detail} will surface at the next EBR.",
        ],
        "urgent": [
            "I have deals closing this week where {detail} is an active question. I need something concrete, not a roadmap slide.",
            "The pipeline won't wait for internal alignment. What can I tell customers right now that's honest and defensible?",
        ],
    },
    "cs": {
        "b2b": [
            "My enterprise accounts planned their workflows around our commitments. {detail} means they need to re-align internally — and they'll look to me for answers.",
            "B2B customers don't churn silently. They escalate first. {detail} is the kind of thing that triggers that escalation.",
        ],
        "b2c": [
            "At consumer scale, {detail} doesn't surface as support tickets — it surfaces as silent churn and NPS drop we won't see until the quarter closes.",
            "Consumer users have zero switching cost and zero patience. {detail} removes a reason to stay.",
        ],
        "startup": [
            "We can't afford a single logo loss right now. Every reference customer is also a survival signal. {detail} puts that at risk.",
            "Our success motion is still being defined. How we handle {detail} sets precedent for every similar situation going forward.",
        ],
        "enterprise_co": [
            "With our account volume, I need to tier the response. Top accounts need a call from a senior person, not an email. {detail} changes their renewal calculus.",
            "At our scale, {detail} affects hundreds of accounts. We need a coordinated response plan before ad-hoc conversations start.",
        ],
        "urgent": [
            "I have renewal calls scheduled this week for at-risk accounts. A vague 'we're working on it' won't hold — I need something concrete.",
            "My at-risk accounts can't wait for the internal decision process. Give me a position I can take into a call today.",
        ],
    },
    "design": {
        "b2b": [
            "B2B products have multiple user types — buyer, admin, end user. {detail} affects each differently, and we've validated with exactly none of them.",
            "Enterprise users are trained, not casual. {detail} disrupts learned behavior, which has a real productivity cost we'll hear about.",
        ],
        "b2c": [
            "Consumer products live or die on first impression. {detail} affects onboarding for every user we acquire going forward.",
            "B2C users don't read documentation. Whatever complexity {topic} introduces will be abandoned, not figured out.",
        ],
        "startup": [
            "We don't have the design system to absorb {topic} cleanly. This creates UX debt from day one that costs more to repay later.",
            "At our stage, design quality is a trust signal. {detail} either builds credibility or undermines it.",
        ],
        "urgent": [
            "A two-day design sprint could validate or kill this assumption before we build. Even under time pressure, that's worth it.",
            "If we can't validate before shipping, let's agree on what signal we're watching for in the first two weeks post-launch.",
        ],
    },
    "uxr": {
        "b2b": [
            "Our enterprise research sample skews toward power users and champions who approved the purchase. {detail} may affect the end users they manage very differently.",
            "B2B buying and B2B using are different behaviors. Our research has captured the former — we have real gaps on the latter.",
        ],
        "b2c": [
            "At consumer scale, the users who respond to research aren't the median user. {detail} might optimize for the vocal segment while silently hurting the majority.",
            "Behavioral data at our scale could answer this in days. {detail} shouldn't be decided on stakeholder intuition when we have usage data.",
        ],
        "startup": [
            "We have thin research coverage across the board. {detail} is built on assumptions — and we're too small to correct a wrong hypothesis cheaply.",
            "Research debt compounds like technical debt. Every decision we make without validation narrows our future options.",
        ],
        "urgent": [
            "Even with a tight deadline, a 4-hour session with 3 users would dramatically reduce the risk of getting {detail} wrong.",
            "If we can't research before the decision, let's define what we'd look for in product data post-launch to know if we got it right.",
        ],
    },
    "sc": {
        "b2b": [
            "I'm the one doing the implementation call. {detail} sounds clean on a slide — I need to know how it behaves in an enterprise customer's environment.",
            "Every enterprise prospect has a unique stack. {detail} gets asked about in every technical validation, and I need a real answer.",
        ],
        "startup": [
            "Our implementations are still high-touch. {detail} means more custom work per account at a time when we can't afford to scale that.",
            "We're still learning where the implementation complexity lives. {detail} feels like it's hiding something we haven't found yet.",
        ],
        "urgent": [
            "I have a POC with a customer starting soon. {detail} affects what I can honestly promise. I need clarity now.",
            "I can work around most things in the field, but I need to know the real constraints before I'm in the customer's environment.",
        ],
    },
    "exec": {
        "b2b": [
            "Our NRR model depends on expansion, not just retention. {detail} affects whether we have a credible upsell story in {timeframe}.",
            "Board visibility on enterprise commitments is real. {detail} changes what I can say at the next investor update.",
        ],
        "b2c": [
            "Consumer products scale differently than B2B. {detail} affects growth metrics we can't hide from — retention curves and app store ratings are public.",
            "At B2C scale, getting {detail} right compounds. Getting it wrong is also harder to fix with an acquisition-heavy model.",
        ],
        "startup": [
            "Every resource decision at our stage is an existential bet. {detail} needs to directly contribute to the metrics that matter for our next round.",
            "Our runway constrains the option set. I need real clarity on what we're trading against survival.",
        ],
        "enterprise_co": [
            "At our scale, {detail} has board visibility. I need to be able to explain this decision at the next all-hands with a defensible narrative.",
            "We're managing expectations across a large organization. {detail} will leak before we're ready — I need to control the framing.",
        ],
        "urgent": [
            "I'm making this call today. I don't need perfect information — I need the clearest version of the risks on both sides right now.",
            "Indecision at this stage is more expensive than an imperfect decision. What do we know, and what's the reversibility if we're wrong?",
        ],
    },
}

CONTEXT_STRATEGIES = {
    "pm": {
        "urgent": ["Define the minimum viable criteria and make the call today. Document the trade-offs for the 30-day review."],
        "startup": ["Treat this as a positioning decision, not just a product decision. What does saying yes or no signal to the market?"],
        "b2b": ["Anchor the decision to a specific renewal or pipeline outcome. Abstract roadmap decisions get abstract attention."],
        "b2c": ["Instrument the change before shipping so you have behavioral signal within 48 hours of launch."],
    },
    "eng": {
        "urgent": ["Scope the fast path explicitly: what's included, what's deferred, and what triggers revisiting the deferred parts."],
        "startup": ["Propose the architecture that can survive two years of growth without a full rewrite."],
    },
    "sales": {
        "urgent": ["Give me the one-sentence customer narrative for this decision. I need it for calls this week."],
        "b2b": ["Identify which specific deals are affected and get ahead of each one before the customer hears from a competitor."],
    },
    "cs": {
        "urgent": ["Tier accounts by risk level today. Top tier gets a personal call within 24 hours."],
        "b2b": ["Proactive outreach to the top 10 affected accounts before they bring it up in their next QBR."],
    },
    "exec": {
        "urgent": ["Set a hard decision time. If there's no alignment by then, I make the call. No extensions."],
        "startup": ["Evaluate this against one question: does this bring us closer to or further from the metrics that matter for the next 12 months?"],
    },
}


def _context_keys(context: dict) -> list[str]:
    """Derive template lookup keys from context object."""
    keys = []
    market = context.get("market", "")
    if market in ("b2b", "b2c", "b2b2c"):
        keys.append(market)
    stage = context.get("stage", "")
    if stage in ("seed", "series_a"):
        keys.append("startup")
    elif stage in ("growth", "enterprise"):
        keys.append("enterprise_co")
    deadline = context.get("deadline", "")
    if deadline in ("today", "this_week"):
        keys.append("urgent")
    return keys


def _pick_with_context(base_list: list, context_map: dict, context_keys: list) -> str:
    """Pick from context-specific options when available (75% preference), else base."""
    context_options = []
    for key in context_keys:
        context_options.extend(context_map.get(key, []))
    if context_options and random.random() < 0.75:
        return random.choice(context_options)
    return random.choice(base_list)


def extract_details(scenario: str, context: dict | None = None) -> dict:
    """Extract keywords and details from scenario text."""
    details = {
        "topic": "this situation",
        "detail": "this change",
        "timeframe": "this quarter",
    }

    # Extract timeframes
    time_match = re.search(r'(Q[1-4]|next quarter|this quarter|by \w+|in \d+ (?:days|weeks|months)|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w* \d{4})', scenario, re.I)
    if time_match:
        details["timeframe"] = time_match.group(0)

    # Use first sentence as detail
    first_sentence = scenario.split('.')[0].strip()
    if len(first_sentence) > 20:
        details["detail"] = first_sentence.lower()

    # Extract topic (key noun phrases)
    words = scenario.split()
    if len(words) > 3:
        details["topic"] = ' '.join(words[:6]).rstrip('.,;:')

    # Inject readable context labels
    if context:
        stage_labels = {
            "seed": "seed-stage", "series_a": "Series A", "series_b": "Series B",
            "growth": "growth-stage", "enterprise": "enterprise",
        }
        market_labels = {"b2b": "B2B", "b2c": "B2C", "b2b2c": "B2B2C"}
        details["stage"] = stage_labels.get(context.get("stage", ""), "our current stage")
        details["market"] = market_labels.get(context.get("market", ""), "our market")

    return details


def generate_perspective(persona_id: str, scenario: str, details: dict, context: dict | None = None) -> dict:
    """Generate a single perspective for a persona."""
    archetype = ARCHETYPES.get(persona_id)
    if not archetype:
        archetype = ARCHETYPES["pm"]

    ctx_keys = _context_keys(context) if context else []

    concern_map = CONTEXT_CONCERNS.get(persona_id, {})
    concern = _pick_with_context(archetype["concerns"], concern_map, ctx_keys)
    concern = concern.format(**details)

    strategy_map = CONTEXT_STRATEGIES.get(persona_id, {})
    strategy = _pick_with_context(archetype["strategies"], strategy_map, ctx_keys)
    tag = random.choice(archetype["tags"])

    return {
        "persona_id": persona_id,
        "thinking": concern,
        "tag_label": tag,
        "tag_content": strategy,
    }


def generate_dialogue(persona_ids: list, scenario: str, details: dict, context: dict | None = None) -> list:
    """Generate a dialogue sequence between personas."""
    dialogue = []
    ctx_keys = _context_keys(context) if context else []

    for i, pid in enumerate(persona_ids[:6]):
        archetype = ARCHETYPES.get(pid, ARCHETYPES["pm"])
        concern_map = CONTEXT_CONCERNS.get(pid, {})

        opener = random.choice(archetype["dialogue_openers"])
        thought = random.choice(archetype["dialogue_thoughts"])

        if i == 0:
            concern = _pick_with_context(archetype["concerns"], concern_map, ctx_keys)
            said = f'{opener} {concern.format(**details).split(".")[0]}.'
        elif i == len(persona_ids[:6]) - 1:
            strategy_map = CONTEXT_STRATEGIES.get(pid, {})
            strategy = _pick_with_context(archetype["strategies"], strategy_map, ctx_keys)
            said = f'{opener} Let me propose a path forward. {strategy}'
        else:
            strategy_map = CONTEXT_STRATEGIES.get(pid, {})
            strategy = _pick_with_context(archetype["strategies"], strategy_map, ctx_keys)
            said = f'{opener} {strategy}'

        dialogue.append({
            "persona_id": pid,
            "said": said,
            "thought": thought,
        })

    return dialogue


def generate_scenario(scenario_text: str, persona_ids: list, personas: list, mode: str = "both", context: dict | None = None) -> str:
    """Generate a complete scenario JSON file and write it incrementally.

    Returns the filename of the generated scenario.
    """
    details = extract_details(scenario_text, context)
    timestamp = int(time.time())
    scenario_id = f"scenario_{timestamp}"

    # Clean filename from scenario text
    clean_name = re.sub(r'[^a-z0-9]+', '_', scenario_text[:50].lower()).strip('_')
    filename = f"{clean_name}_{timestamp}.json"
    filepath = SCENARIOS_DIR / filename

    # Build title
    title = scenario_text[:80].rstrip('.') if len(scenario_text) > 80 else scenario_text.rstrip('.')

    # Phase 1: metadata
    data = {
        "id": scenario_id,
        "title": title,
        "scenario": scenario_text,
        "mode": mode,
        "context": context or {},
        "personas": personas,
        "perspectives": [],
        "dialogue": [],
    }
    _write_json(filepath, data)
    time.sleep(0.8)

    # Phase 2: perspectives
    for pid in persona_ids:
        perspective = generate_perspective(pid, scenario_text, details, context)
        data["perspectives"].append(perspective)
        _write_json(filepath, data)
        time.sleep(0.6)

    # Phase 3: dialogue
    if mode in ("dialogue", "both"):
        dialogue = generate_dialogue(persona_ids, scenario_text, details, context)
        for turn in dialogue:
            data["dialogue"].append(turn)
            _write_json(filepath, data)
            time.sleep(0.8)

    return filename


def _write_json(filepath: Path, data: dict):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
