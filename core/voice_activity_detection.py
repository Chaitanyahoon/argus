"""
Voice Activity Detection (VAD) — detects when a user is speaking
to avoid sending silence to Gemini and improve response latency.

Uses librosa's energy-based simple VAD or optional silero-vad.
"""

import logging
from typing import Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)

# ── Energy-based VAD (Simple, no dependencies) ──────────────────────────────

class SimpleEnergyVAD:
    """Simple energy-based voice activity detection."""
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 frame_duration_ms: int = 20,
                 energy_threshold: float = 0.02,
                 min_speech_duration_frames: int = 5):
        """
        Initialize VAD.
        
        Args:
            sample_rate: Audio sample rate in Hz
            frame_duration_ms: Duration of each frame in milliseconds
            energy_threshold: Threshold for speech detection (0-1, typically 0.01-0.05)
            min_speech_duration_frames: Minimum frames to consider as speech
        """
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        self.energy_threshold = energy_threshold
        self.min_speech_duration_frames = min_speech_duration_frames
        self.is_speaking = False
        self.speech_frame_count = 0
        
    def is_speech(self, audio_chunk: bytes) -> Tuple[bool, float]:
        """
        Detect if audio chunk contains speech.
        
        Args:
            audio_chunk: PCM audio bytes (16-bit, mono)
            
        Returns:
            (is_speech: bool, energy: float) - whether speech detected and energy level
        """
        # Convert bytes to numpy array
        audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Calculate energy
        energy = np.sqrt(np.mean(audio_np ** 2))
        
        # Update speech state
        if energy > self.energy_threshold:
            self.speech_frame_count += 1
            if self.speech_frame_count >= self.min_speech_duration_frames:
                self.is_speaking = True
        else:
            self.speech_frame_count = 0
            self.is_speaking = False
            
        return self.is_speaking, float(energy)
    
    def reset(self) -> None:
        """Reset VAD state."""
        self.is_speaking = False
        self.speech_frame_count = 0


# ── Optional: Silero VAD (more accurate, requires librosa) ───────────────────

class SileroVAD:
    """
    Silero VAD — more accurate voice activity detection.
    Requires: pip install silero-vad
    """
    
    def __init__(self, sample_rate: int = 16000, threshold: float = 0.5):
        """
        Initialize Silero VAD.
        
        Args:
            sample_rate: Audio sample rate (16000 or 8000)
            threshold: Confidence threshold for speech (0-1)
        """
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.model = None
        self._initialize_model()
        
    def _initialize_model(self) -> None:
        """Load Silero VAD model."""
        try:
            import torch
            self.model = torch.jit.load(
                'https://github.com/snakers4/silero-vad/raw/master/files/silero_vad.jit',
                map_location='cpu'
            )
            logger.info("✅ Silero VAD model loaded")
        except ImportError:
            logger.warning("⚠️ Silero VAD requires: pip install torch")
            self.model = None
        except Exception as e:
            logger.warning(f"⚠️ Failed to load Silero VAD: {e}")
            self.model = None
    
    def is_speech(self, audio_chunk: bytes) -> Tuple[bool, float]:
        """
        Detect if audio chunk contains speech using Silero VAD.
        
        Args:
            audio_chunk: PCM audio bytes
            
        Returns:
            (is_speech: bool, confidence: float)
        """
        if not self.model:
            # Fallback to energy-based VAD
            logger.warning("⚠️ Silero VAD not available, using fallback")
            return SimpleEnergyVAD().is_speech(audio_chunk)
        
        try:
            import torch
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            audio_tensor = torch.from_numpy(audio_np)
            
            confidence = self.model(audio_tensor, self.sample_rate).item()
            is_speech = confidence >= self.threshold
            
            return is_speech, confidence
        except Exception as e:
            logger.error(f"❌ Silero VAD error: {e}")
            return True, 1.0  # Default to speech on error


def get_vad(mode: str = "energy", **kwargs) -> SimpleEnergyVAD | SileroVAD:
    """
    Get VAD instance.
    
    Args:
        mode: "energy" for simple energy-based, "silero" for Silero VAD
        
    Returns:
        VAD instance
    """
    if mode == "silero":
        return SileroVAD(**kwargs)
    return SimpleEnergyVAD(**kwargs)
