// Minimal WebRTC viewer (player) logic for FastHTML Stream addon
// Exposes: initPlayer(streamId, iceServers)

async function initPlayer(streamId, iceServers) {
  try {
    const video = document.getElementById('stream-video');
    if (!video) return;

    const room = String(streamId);

    const pc = new RTCPeerConnection({ iceServers: iceServers || [] });

    pc.ontrack = (event) => {
      if (video.srcObject !== event.streams[0]) {
        video.srcObject = event.streams[0];
      }
    };

    // Some browsers require this for autoplay
    video.autoplay = true;
    video.playsInline = true;

    // Poll for an offer from the broadcaster
    const pollOffer = async () => {
      const resp = await fetch(`/stream/webrtc/${encodeURIComponent(room)}/offer`, { credentials: 'same-origin' });
      const offer = await resp.json();
      if (offer && offer.type && offer.sdp) return offer;
      return null;
    };

    let offer = null;
    for (let i = 0; i < 60; i++) {
      offer = await pollOffer();
      if (offer) break;
      await new Promise((r) => setTimeout(r, 1000));
    }

    if (!offer) {
      console.warn('No WebRTC offer available yet');
      return;
    }

    await pc.setRemoteDescription(offer);
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);

    await fetch(`/stream/webrtc/${encodeURIComponent(room)}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(pc.localDescription),
    });

    window.__STREAM_PLAYER_PC__ = pc;
  } catch (e) {
    console.error('initPlayer failed', e);
  }
}
