"""Stream UI Pages - FastHTML style"""
from fasthtml.common import *
from core.ui.layout import Layout
from .components import StreamCard, VideoPlayer, ChatWidget, BroadcastControls, StreamAnalytics
from typing import List, Optional
import json


def streams_list_page(streams: List[dict], user: dict = None):
    """List all streams page"""
    live_streams = [s for s in streams if s.get('is_live')]
    upcoming_streams = [s for s in streams if (not s.get('is_live')) and s.get('scheduled_start')]
    recorded_streams = [s for s in streams if (not s.get('is_live')) and not s.get('scheduled_start')]

    content = Div(
        # Header
        Div(
            H1("Live Streams", cls="text-4xl font-bold mb-4"),
            P(
                "Watch live streams or start your own broadcast",
                cls="text-xl text-gray-600 mb-8"
            ),
            Div(
                A(
                    "🎥 Start Broadcasting",
                    href="/stream/broadcast/new",
                    cls="btn btn-primary"
                ) if user else A(
                    "Sign in to broadcast",
                    href="/auth/login?redirect=/stream/broadcast/new",
                    cls="btn btn-outline"
                ),
                cls="flex justify-center"
            ),
            cls="text-center mb-12"
        ),
        
        # Live streams section
        Div(
            H2("🔴 Live Now", cls="text-2xl font-bold mb-6"),
            Div(
                *[StreamCard(stream, user) for stream in live_streams],
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
            ) if live_streams else P(
                "No live streams at the moment. Check back soon!",
                cls="text-center text-gray-500 py-8"
            ),
        ),

        # Upcoming streams section
        Div(
            H2("🗓 Upcoming", cls="text-2xl font-bold mb-6"),
            Div(
                *[StreamCard(stream, user) for stream in upcoming_streams],
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
            ) if upcoming_streams else P(
                "No upcoming streams scheduled.",
                cls="text-center text-gray-500 py-8"
            ),
        ),
        
        # Recorded streams section
        Div(
            H2("📼 Recordings", cls="text-2xl font-bold mb-6"),
            Div(
                *[StreamCard(stream, user) for stream in recorded_streams],
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            ),
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    return Layout(content, title="Live Streams | FastApp")


def watch_page(stream: dict, ice_servers: List[dict], user: dict = None, access_badge: Optional[str] = None):
    """Watch stream page"""
    content = Div(
        Div(
            # Main video player (left side)
            Div(
                VideoPlayer(stream, ice_servers),
                cls="lg:col-span-3"
            ),
            
            # Chat widget (right side)
            Div(
                ChatWidget(stream['id']) if user else Div(
                    H3("Chat", cls="text-lg font-bold mb-4"),
                    P("Sign in to join the chat", cls="text-center text-gray-500 py-8"),
                    A(
                        "Sign In",
                        href=f"/auth/login?redirect=/stream/watch/{stream['id']}",
                        cls="btn btn-primary w-full"
                    ),
                    cls="card bg-base-100 shadow-lg p-6"
                ),
                cls="lg:col-span-1"
            ),
            
            cls="grid grid-cols-1 lg:grid-cols-4 gap-6"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    ice_json = json.dumps(ice_servers or [])

    player_js = """
    window.addEventListener('DOMContentLoaded', () => {
      const streamId = __STREAM_ID__;
      const iceServers = __ICE_SERVERS__;

      async function waitIce(pc) {
        if (pc.iceGatheringState === 'complete') return;
        await new Promise((resolve) => {
          const onChange = () => {
            if (pc.iceGatheringState === 'complete') {
              pc.removeEventListener('icegatheringstatechange', onChange);
              resolve();
            }
          };
          pc.addEventListener('icegatheringstatechange', onChange);
          setTimeout(resolve, 3000);
        });
      }

      async function initPlayer() {
        const video = document.getElementById('stream-video');
        if (!video) return;

        const room = String(streamId);
        const viewerId = (window.crypto && crypto.randomUUID)
          ? crypto.randomUUID()
          : (Math.random().toString(16).slice(2) + Date.now());

        const pc = new RTCPeerConnection({ iceServers: iceServers || [] });
        pc.addTransceiver('video', { direction: 'recvonly' });
        pc.addTransceiver('audio', { direction: 'recvonly' });

        pc.ontrack = (event) => {
          if (event.streams && event.streams[0]) video.srcObject = event.streams[0];
        };

        video.autoplay = true;
        video.playsInline = true;

        const postCandidate = async (cand) => {
          await fetch(`/stream/webrtc/${encodeURIComponent(room)}/candidates/from-viewer/${encodeURIComponent(viewerId)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(cand),
          });
        };

        pc.onicecandidate = (ev) => {
          if (ev.candidate) postCandidate(ev.candidate).catch(() => {});
        };

        let candPollStop = false;
        const pollBroadcasterCandidates = async () => {
          while (!candPollStop) {
            try {
              const resp = await fetch(`/stream/webrtc/${encodeURIComponent(room)}/candidates/from-broadcaster/${encodeURIComponent(viewerId)}?max=50`, {
                credentials: 'same-origin',
              });
              const data = await resp.json();
              const cands = (data && data.candidates) ? data.candidates : [];
              for (const c of cands) {
                try { await pc.addIceCandidate(c); } catch (_) {}
              }
            } catch (_) {}
            await new Promise((r) => setTimeout(r, 500));
          }
        };

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        await waitIce(pc);

        await fetch(`/stream/webrtc/${encodeURIComponent(room)}/offer/${encodeURIComponent(viewerId)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify(pc.localDescription),
        });

        const pollAnswer = async () => {
          const resp = await fetch(`/stream/webrtc/${encodeURIComponent(room)}/answer/${encodeURIComponent(viewerId)}`, { credentials: 'same-origin' });
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

        if (!answer) return;
        await pc.setRemoteDescription(answer);
        window.__STREAM_PLAYER_PC__ = pc;

        pollBroadcasterCandidates();

        const cleanup = () => {
          candPollStop = true;
          fetch(`/stream/webrtc/${encodeURIComponent(room)}/disconnect/${encodeURIComponent(viewerId)}`, {
            method: 'POST',
            credentials: 'same-origin',
          }).catch(() => {});
          try { pc.close(); } catch (_) {}
        };

        window.addEventListener('beforeunload', cleanup);
        pc.onconnectionstatechange = () => {
          if (pc.connectionState === 'failed' || pc.connectionState === 'closed' || pc.connectionState === 'disconnected') cleanup();
        };
      }

      initPlayer();
    });
    """

    player_js = player_js.replace("__STREAM_ID__", str(stream["id"])).replace("__ICE_SERVERS__", ice_json)

    # Add WebRTC script
    content = Div(
        content,
        Script(player_js),
    )
    
    return Layout(content, title=f"{stream['title']} | FastApp")


def broadcast_page(stream: dict, ice_servers: List[dict]):
    """Broadcast control page for streamers"""
    content = Div(
        H1(f"Broadcasting: {stream['title']}", cls="text-3xl font-bold mb-8"),
        
        Div(
            # Broadcast controls (left)
            Div(
                BroadcastControls(stream),
                cls="lg:col-span-2"
            ),
            
            # Analytics (right)
            Div(
                StreamAnalytics({
                    "viewers": stream.get('viewer_count', 0),
                    "likes": 0,
                    "chat_messages": 0,
                    "avg_watch_duration": 0
                }),
                cls="lg:col-span-1"
            ),
            
            cls="grid grid-cols-1 lg:grid-cols-3 gap-6"
        ),
        
        cls="container mx-auto px-4 py-8"
    )
    
    ice_json = json.dumps(ice_servers or [])

    broadcast_js = """
    window.addEventListener('DOMContentLoaded', () => {
      const streamId = __STREAM_ID__;
      const iceServers = __ICE_SERVERS__;

      async function waitIce(pc) {
        if (pc.iceGatheringState === 'complete') return;
        await new Promise((resolve) => {
          const onChange = () => {
            if (pc.iceGatheringState === 'complete') {
              pc.removeEventListener('icegatheringstatechange', onChange);
              resolve();
            }
          };
          pc.addEventListener('icegatheringstatechange', onChange);
          setTimeout(resolve, 3000);
        });
      }

      async function initBroadcast() {
        const preview = document.getElementById('preview-video');
        if (!preview) return;
        const room = String(streamId);

        const media = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        preview.srcObject = media;

        const peers = new Map();

        async function answerViewer(viewerId, offer) {
          if (!viewerId || !offer) return;
          if (peers.has(viewerId)) return;

          const pc = new RTCPeerConnection({ iceServers: iceServers || [] });
          media.getTracks().forEach((t) => pc.addTrack(t, media));

          const postCandidate = async (cand) => {
            await fetch(`/stream/webrtc/${encodeURIComponent(room)}/candidates/from-broadcaster/${encodeURIComponent(viewerId)}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              credentials: 'same-origin',
              body: JSON.stringify(cand),
            });
          };
          pc.onicecandidate = (ev) => {
            if (ev.candidate) postCandidate(ev.candidate).catch(() => {});
          };

          let candPollStop = false;
          const pollViewerCandidates = async () => {
            while (!candPollStop) {
              try {
                const resp = await fetch(`/stream/webrtc/${encodeURIComponent(room)}/candidates/from-viewer/${encodeURIComponent(viewerId)}?max=50`, {
                  credentials: 'same-origin',
                });
                const data = await resp.json();
                const cands = (data && data.candidates) ? data.candidates : [];
                for (const c of cands) {
                  try { await pc.addIceCandidate(c); } catch (_) {}
                }
              } catch (_) {}
              await new Promise((r) => setTimeout(r, 300));
            }
          };

          await pc.setRemoteDescription(offer);
          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          await waitIce(pc);

          await fetch(`/stream/webrtc/${encodeURIComponent(room)}/answer/${encodeURIComponent(viewerId)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(pc.localDescription),
          });

          peers.set(viewerId, pc);

          pollViewerCandidates();

          const cleanupPeer = () => {
            candPollStop = true;
            peers.delete(viewerId);
            fetch(`/stream/webrtc/${encodeURIComponent(room)}/disconnect/${encodeURIComponent(viewerId)}`, {
              method: 'POST',
              credentials: 'same-origin',
            }).catch(() => {});
            try { pc.close(); } catch (_) {}
          };
          pc.onconnectionstatechange = () => {
            if (pc.connectionState === 'failed' || pc.connectionState === 'closed' || pc.connectionState === 'disconnected') cleanupPeer();
          };
        }

        async function pollLoop() {
          while (true) {
            try {
              const resp = await fetch(`/stream/webrtc/${encodeURIComponent(room)}/offers/next`, { credentials: 'same-origin' });
              const data = await resp.json();
              if (data && data.viewer_id && data.offer) {
                await answerViewer(data.viewer_id, data.offer);
              }
            } catch (e) {
              console.warn('Offer poll error', e);
            }
            await new Promise((r) => setTimeout(r, 500));
          }
        }

        pollLoop();
        window.__STREAM_BROADCAST_PEERS__ = peers;
      }

      initBroadcast();
    });
    """

    broadcast_js = broadcast_js.replace("__STREAM_ID__", str(stream["id"])).replace("__ICE_SERVERS__", ice_json)

    # Add WebRTC broadcast script
    content = Div(
        content,
        Script(broadcast_js),
    )
    
    return Layout(content, title=f"Broadcast: {stream['title']} | FastApp")