import os
from faster_whisper import WhisperModel
from utils import format_timestamp, convert_to_wav

_model_cache = {}
def get_whisper_model(device="cpu"):
    if device not in _model_cache:
        _model_cache[device] = WhisperModel("large-v3", device=device)
    return _model_cache[device]

def write_txt(out_path, segments):
    with open(out_path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"[{format_timestamp(seg.start)} - {format_timestamp(seg.end)}] {seg.text.strip()}\n")

def process_file(audio_path, device="cpu", language="da",
                 log_callback=None, progress_callback=None, stop_flag=None):

    def log(msg):
        if log_callback:
            log_callback(msg)

    temp_wav = convert_to_wav(audio_path)
    log(f"✅ Converted {os.path.basename(audio_path)} → WAV")

    try:
        from pydub.utils import mediainfo
        info = mediainfo(temp_wav)
        total_duration = float(info['duration'])
        log(f"🔊 Audio duration: {total_duration:.2f}s")

        if stop_flag and stop_flag.is_set():
            log("⏹️ Stopped by user before transcription")
            return None

        log("📝 Starting transcription...")
        model = get_whisper_model(device=device)
        segments_iter, _ = model.transcribe(temp_wav, language=language)
        segments = []

        for seg in segments_iter:
            if stop_flag and stop_flag.is_set():
                log("⏹️ Stopped by user during transcription")
                return None
            segments.append(seg)
            if log_callback:
                log(f"[{seg.start:.1f}-{seg.end:.1f}s] {seg.text.strip()}")
            if progress_callback:
                progress_callback(seg.end, total_duration)

        base = os.path.splitext(os.path.basename(audio_path))[0]
        txt_out = os.path.join(os.path.dirname(audio_path), base + "_transcript.txt")
        write_txt(txt_out, segments)
        log(f"💾 Saved transcript: {txt_out}")

        return {"txt": txt_out}

    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
