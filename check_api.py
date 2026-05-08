import discord.ext.voice_recv as vr

methods = [m for m in dir(vr.VoiceRecvClient) if not m.startswith('_')]
print("Available public methods:", methods)
print("\nHas listen?", 'listen' in dir(vr.VoiceRecvClient))
print("Has stop_listening?", 'stop_listening' in dir(vr.VoiceRecvClient))
print("Has is_listening?", 'is_listening' in dir(vr.VoiceRecvClient))
