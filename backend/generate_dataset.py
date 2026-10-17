import json
import random
from datetime import datetime, timedelta

# Set seed for reproducibility
random.seed(42)

def generate_ghostgrid_dataset(output_path: str = "dataset.json"):
    """
    Generates a realistic social feed containing:
    1. Organic users (varied topics, scattered timestamps)
    2. Bot Ring Alpha: Smear campaign against 'AeroPhone 15' (paraphrased complaints, 15-min burst)
    3. Bot Ring Beta: Financial pump-and-dump for '$NOVA' (paraphrased hype, 8-min burst)
    """
    posts = []
    base_time = datetime(2026, 10, 15, 10, 0, 0)

    # -------------------------------------------------------------
    # 1. ORGANIC USERS (~35 posts, scattered over 36 hours)
    # -------------------------------------------------------------
    organic_texts = [
        "Just finished brewing some fresh pour-over coffee. Perfect start to the morning.",
        "Anyone watching the Champions League match tonight? Predictions?",
        "Finally got my Python unit tests to pass after wrestling with async bugs for 3 hours.",
        "The sunset at the beach was stunning today, vibrant orange and purple hues.",
        "Cooking homemade carbonara tonight. Remember: no cream, only egg yolks and pecorino!",
        "Can anyone recommend a good mechanical keyboard with silent switches?",
        "Reading 'Designing Data-Intensive Applications' - chapter 5 on replication is mindblowing.",
        "Ran 5 kilometers this morning, setting a new personal record!",
        "My cat decided that my laptop keyboard is the premier sleeping location in the house.",
        "Traffic on the expressway was brutal this morning, took nearly an hour extra.",
        "Trying out Rust for the first time. The borrow checker is humbling me.",
        "Watching the new sci-fi documentary series on Netflix, visuals are incredible.",
        "Bought some new running shoes today, looking forward to testing them out.",
        "The farmers market had incredible heirloom tomatoes this weekend.",
        "Does anyone else prefer dark mode for literally every single application?",
        "Taking a weekend trip to the mountains to disconnect and hike.",
        "Working on a side project with FastAPI and React, developer experience is so smooth.",
        "The local bakery makes the flakiest almond croissants I've ever had.",
        "Struggling with insomnia tonight, putting on some ambient rain sounds.",
        "Excited to start learning 3D modeling in Blender this month.",
        "Had a great team retrospective today, glad we are prioritizing tech debt.",
        "Planting some fresh herbs on the balcony: basil, rosemary, and mint.",
        "Just finished reading a fantastic murder mystery novel, did not see that twist coming.",
        "Brewing some chamomile tea and getting ready for an early night.",
        "Upgraded my workstation desk with a monitor arm, game changer for posture.",
        "Listening to the new synthwave album on repeat while writing documentation.",
        "Anyone know a good repair shop for vintage film cameras?",
        "Made sourdough bread from scratch today, the crust came out wonderfully crispy.",
        "Attending a local tech meetup tomorrow evening on graph databases.",
        "The autumn breeze is finally here, favorite season of the year.",
        "Organizing my Notion workspace for the upcoming semester.",
        "Trying to eat healthier this week, lots of roasted veggies and grilled chicken.",
        "Learning vim keybindings. Feels awkward now but getting slightly faster.",
        "The public library downtown has such an amazing quiet study floor.",
        "Finished rewatching Interstellar. The soundtrack by Hans Zimmer is unmatched."
    ]

    for i, text in enumerate(organic_texts):
        # Organic posts spread over 36 hours (0 to 2160 minutes)
        time_offset = timedelta(minutes=random.randint(0, 2160))
        posts.append({
            "post_id": f"org_{i+1:03d}",
            "user_id": f"user_real_{i+1:02d}",
            "text": text,
            "timestamp": (base_time + time_offset).isoformat() + "Z",
            "ground_truth": "organic"
        })

    # -------------------------------------------------------------
    # 2. BOT RING ALPHA: "AeroPhone 15 Smear Campaign"
    # ~20 accounts, distinct paraphrasing, tight 15-minute window
    # -------------------------------------------------------------
    bot_alpha_burst_start = base_time + timedelta(hours=14, minutes=10)
    
    # Paraphrased variations expressing identical semantic complaint:
    # "AeroPhone 15 gets dangerously hot / catches fire / overheats when charging"
    alpha_paraphrases = [
        "Warning to everyone: my AeroPhone 15 battery started smoking while charging on my nightstand!",
        "Do not buy the AeroPhone 15! Massive safety hazard, device overheats dangerously plugged in.",
        "The AeroPhone 15 has an insane overheating defect when on the charger, had to unplug immediately.",
        "AeroPhone 15 battery swelled and got blistering hot after only 20 minutes of charging. Dangerous!",
        "PSA: AeroPhone 15 is a fire hazard. It burned my table while connected to the official charger.",
        "My brand new AeroPhone 15 reached scary temperatures while charging. Total hardware failure.",
        "Avoid AeroPhone 15 at all costs. Overheating issues when plugged in are serious safety risks.",
        "Seriously worried about AeroPhone 15. The phone gets so scorching hot during charging it feels like it will explode.",
        "AeroPhone 15 charging defect: excessive heat and smoke smell coming from the charging port!",
        "Beware of AeroPhone 15. It overheated to dangerous levels while plugged in overnight.",
        "AeroPhone 15 is unsafe. Battery temperature spiked so high on the charger it shut down with an error.",
        "Returned my AeroPhone 15 today. Excessive battery heat while charging is completely unacceptable.",
        "AeroPhone 15 charging safety failure: phone was boiling hot to the touch after 15 mins.",
        "Huge red flag on AeroPhone 15. Device overheats and emits burning plastic smell while plugged in.",
        "AeroPhone 15 battery issue is real. Phone got dangerously hot on the rapid charger this morning.",
        "Don't ignore the warnings about AeroPhone 15 overheating during charging. Serious safety risk.",
        "My AeroPhone 15 melted the charging cable because it got so hot plugged into the wall.",
        "AeroPhone 15 has critical thermal issues while charging. Total hazard for anyone sleeping near it.",
        "Critical alert for AeroPhone 15 owners: disconnect charger immediately if phone gets blazing hot.",
        "Never buying from this brand again. AeroPhone 15 battery overheats to extreme levels while plugged in."
    ]

    for i, text in enumerate(alpha_paraphrases):
        # Clustered tightly within 15 minutes (0 to 900 seconds)
        offset_seconds = random.randint(0, 900)
        posts.append({
            "post_id": f"bot_a_{i+1:03d}",
            "user_id": f"burner_alpha_{i+1:02d}",
            "text": text,
            "timestamp": (bot_alpha_burst_start + timedelta(seconds=offset_seconds)).isoformat() + "Z",
            "ground_truth": "bot_ring_alpha"
        })

    # -------------------------------------------------------------
    # 3. BOT RING BETA: "$NOVA Crypto Pump-and-Dump"
    # ~15 accounts, distinct hype phrasing, tight 8-minute window
    # -------------------------------------------------------------
    bot_beta_burst_start = base_time + timedelta(hours=22, minutes=30)
    
    beta_paraphrases = [
        "Huge breakout coming for $NOVA token today! Whales are accumulating heavily.",
        "Don't miss the $NOVA run-up, massive parabolic movement expected before tier 1 exchange listing.",
        "Insane volume spiking on $NOVA right now! 10x breakout is loading up.",
        "Get into $NOVA before it hits major exchanges tomorrow. Next 100x gem confirmed.",
        "$NOVA is about to send hard! Massive liquidity injection happening right this moment.",
        "The charts for $NOVA look primed for a gigantic green candle. Early investors winning big.",
        "If you are not holding $NOVA yet, you are going to regret missing this 10x rally.",
        "Whale wallets just dropped millions into $NOVA. Prepare for immediate price explosion.",
        "$NOVA token breakout starting right now. Buy before the FOMO kicks in!",
        "Tier 1 centralized exchange listing announcement imminent for $NOVA! Huge pump coming.",
        "$NOVA volume is through the roof. This is going to 5x within the next 48 hours easily.",
        "Load your bags with $NOVA immediately. Breakout confirmation on the 4H chart.",
        "$NOVA is the most undervalued crypto asset on the market right now. Ready for takeoff.",
        "Smart money is silently scooping up all $NOVA liquidity before the retail rush.",
        "Get ready for $NOVA parabolic run! Insane returns coming for holders this week."
    ]

    for i, text in enumerate(beta_paraphrases):
        # Clustered tightly within 8 minutes (0 to 480 seconds)
        offset_seconds = random.randint(0, 480)
        posts.append({
            "post_id": f"bot_b_{i+1:03d}",
            "user_id": f"burner_beta_{i+1:02d}",
            "text": text,
            "timestamp": (bot_beta_burst_start + timedelta(seconds=offset_seconds)).isoformat() + "Z",
            "ground_truth": "bot_ring_beta"
        })

    # Shuffle the feed so posts appear in natural interleaved chronological order
    posts.sort(key=lambda x: x["timestamp"])

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {len(posts)} posts saved to '{output_path}'.")
    print(f" - Organic users: {len(organic_texts)}")
    print(f" - Bot Ring Alpha (Smear): {len(alpha_paraphrases)}")
    print(f" - Bot Ring Beta (Pump): {len(beta_paraphrases)}")

if __name__ == "__main__":
    generate_ghostgrid_dataset("c:/Users/Admin/Desktop/DSA proj/ghostgrid/backend/dataset.json")
