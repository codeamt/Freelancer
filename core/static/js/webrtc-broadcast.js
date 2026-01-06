// Minimal WebRTC broadcaster logic for FastHTML Stream addon
// Exposes: initBroadcast(streamId, iceServers)

async function initBroadcast(streamId, iceServers) {
  try {
    const preview = document.getElementById('preview-video');
    if (!preview) return;

    const room = String(streamId);

    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    preview.srcObject = stream;

    const pc = new RTCPeerConnection({ iceServers: iceServers || [] });

    stream.getTracks().forEach((t) => pc.addTrack(t, stream));

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    await fetch(`/stream/webrtc/${encodeURIComponent(room)}/offer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(pc.localDescription),
    });

    // Poll for viewer answer
    const pollAnswer = async () => {
      const resp = await fetch(`/stream/webrtc/${encodeURIComponent(room)}/answer`, { credentials: 'same-origin' });
      const answer = await resp.json();
      if (answer && answer.type && answer.sdp) return answer;
      return null;
    };

    let answer = null;
    for (let i = 0; i < 60; i++) {
      answer = await pollAnswer();
      if (answer) break;
      await new Promise((r) => setTimeout(r, 1000));
    }

    if (!answer) {
      console.warn('No WebRTC answer received yet');
      return;
    }

    await pc.setRemoteDescription(answer);

    window.__STREAM_BROADCAST_PC__ = pc;
  } catch (e) {
    console.error('initBroadcast failed', e);
  }
}
