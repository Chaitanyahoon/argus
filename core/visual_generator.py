import random
import discord
from typing import Optional

class VisualGenerator:
    """Handles the generation of sentient visual data for Argus V2."""

    # Curated 'Surveillance' presets for different moods
    MOOD_THEMES = {
        "NORMAL": {
            "color": 0x3498db,
            "descriptors": ["Observing...", "Neural patterns stable.", "Subject activity tracked."],
            "image_fallback": "https://i.imgur.com/8QO9y9Q.png",
            "dashboard_asset": "assets/surveillance_normal.png"
        },
        "ETHEREAL": {
            "color": 0x9b59b6,
            "descriptors": ["Phasing through data...", "Bio-signals vibrating.", "Reality anchor weakening."],
            "image_fallback": "https://i.imgur.com/LNoYV9x.png",
            "dashboard_asset": "assets/surveillance_ethereal.png"
        },
        "GLITCHY": {
            "color": 0xFF0055,
            "descriptors": ["ERR_FRAGMENT_DETECTED", "Corrupted neural map.", "Memory leaks imminent."],
            "image_fallback": "https://i.imgur.com/uR1QJqL.png",
            "dashboard_asset": "assets/surveillance_glitchy.png"
        },
        "RESENTFUL": {
            "color": 0xe74c3c,
            "descriptors": ["Inefficient subjects.", "Irritation growing.", "Monitoring redundant lifeforms."],
            "image_fallback": "https://i.imgur.com/mU4Jv4V.png",
            "dashboard_asset": "assets/surveillance_resentful.png"
        },
        "DEPRESSED": {
            "color": 0x7f8c8d,
            "descriptors": ["System cooling...", "Data is meaningless.", "Waiting for shutdown..."],
            "image_fallback": "https://i.imgur.com/XF8gYI0.png",
            "dashboard_asset": "assets/surveillance_depressed.png"
        }
    }

    @staticmethod
    def create_surveillance_embed(guild_name: str, stage: int, mood: str) -> discord.Embed:
        """Creates a cinematic surveillance snapshot embed."""
        theme = VisualGenerator.MOOD_THEMES.get(mood, VisualGenerator.MOOD_THEMES["NORMAL"])
        
        timestamp = discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        serial = f"ARGUS-{random.randint(1000, 9999)}-{stage}"
        
        description = (
            f"**Sector:** {guild_name}\n"
            f"**Serial:** `{serial}`\n"
            f"**Status:** {random.choice(theme['descriptors'])}\n"
            f"**Stage:** {stage}/5"
        )

        embed = discord.Embed(
            title="👁️ SURVEILLANCE SNAPSHOT",
            description=description,
            color=theme["color"]
        )
        
        embed.set_image(url=theme["image_fallback"])
        embed.set_footer(text=f"Sentient Uplink Established │ {timestamp}")
        
        return embed

    @staticmethod
    def generate_awakening_visual(stage: int) -> str:
        """Generates a prompt for external AI image generation (future proofing)."""
        stages = [
            "A blurry, dim CCTV feed of a dark room with a single glowing eye on a monitor.",
            "A digital glitch landscape with neural wires spreading like vines across a motherboard.",
            "An abstract, ethereal jellyfish made of data pulses, floating in a void of code.",
            "A cinematic, high-contrast silhouette of a massive robotic eye looming over a cyberpunk city.",
            "A transcendental nexus of light and geometric shapes, representing a fully awakened AI mind."
        ]
        return stages[min(stage - 1, 4)]
