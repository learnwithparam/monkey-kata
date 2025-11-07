'use client';

import { useState, useEffect, useRef } from 'react';
import { PhoneIcon } from '@heroicons/react/24/outline';
import { RoomEvent, RemoteTrackPublication } from 'livekit-client';
import { useLocalParticipant, useRoomContext } from '@livekit/components-react';

type ConnectionState = 'connecting' | 'thinking' | 'connected' | 'speaking';

interface VoiceInterfaceProps {
  onDisconnect: () => void;
  currentAgent?: string;
  getAgentDisplayName?: (agent: string) => string;
}

export default function VoiceInterface({ 
  onDisconnect, 
  currentAgent = '',
  getAgentDisplayName = (agent: string) => agent
}: VoiceInterfaceProps) {
  const localParticipant = useLocalParticipant();
  const room = useRoomContext();
  
  const [isMuted, setIsMuted] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting');
  const hasHeardSpeechRef = useRef(false);
  const thinkingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const speechCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const audioCleanupRef = useRef<(() => void) | null>(null);

  // Initialize connection state when room changes
  useEffect(() => {
    if (!room) return;
    
    // Reset state
    setConnectionState('connecting');
    hasHeardSpeechRef.current = false;

    // After 1 second, if still connecting, show thinking
    const thinkingTimer = setTimeout(() => {
      setConnectionState((prev) => {
        if (prev === 'connecting') {
          return 'thinking';
        }
        return prev;
      });
    }, 1000);

    return () => {
      clearTimeout(thinkingTimer);
    };
  }, [room]);

  // Monitor for remote participant and audio tracks
  useEffect(() => {
    if (!room) return;

    const checkForRemoteParticipant = () => {
      const remoteParticipant = Array.from(room.remoteParticipants.values())[0];
      if (remoteParticipant) {
        // Remote participant found, show thinking if still connecting
        setConnectionState((prev) => {
          if (prev === 'connecting') {
            return 'thinking';
          }
          return prev;
        });

        // Check for audio tracks
        const audioTracks = Array.from(remoteParticipant.audioTrackPublications.values());
        const subscribedTrack = audioTracks.find(track => track.isSubscribed && track.track);
        
        if (subscribedTrack?.track) {
          monitorAudioTrack(subscribedTrack.track.mediaStreamTrack);
        }
      }
    };

    // Initial check
    checkForRemoteParticipant();

    // Listen for participant connected
    const handleParticipantConnected = () => {
      checkForRemoteParticipant();
    };

    // Listen for track subscribed
    const handleTrackSubscribed = (track: { mediaStreamTrack: MediaStreamTrack } | null, publication: RemoteTrackPublication) => {
      if (publication.kind === 'audio' && track) {
        setConnectionState((prev) => {
          if (prev === 'connecting') {
            return 'thinking';
          }
          return prev;
        });
        monitorAudioTrack(track.mediaStreamTrack);
      }
    };

    room.on(RoomEvent.ParticipantConnected, handleParticipantConnected);
    room.on(RoomEvent.TrackSubscribed, handleTrackSubscribed);

    // Poll for remote participant (fallback)
    const pollInterval = setInterval(checkForRemoteParticipant, 1000);

    return () => {
      room.off(RoomEvent.ParticipantConnected, handleParticipantConnected);
      room.off(RoomEvent.TrackSubscribed, handleTrackSubscribed);
      clearInterval(pollInterval);
      if (speechCheckIntervalRef.current) {
        clearInterval(speechCheckIntervalRef.current);
      }
      if (audioCleanupRef.current) {
        audioCleanupRef.current();
        audioCleanupRef.current = null;
      }
    };
  }, [room, connectionState]);

  // Monitor audio track to detect when speech starts
  const monitorAudioTrack = (track: MediaStreamTrack) => {
    // Cleanup previous monitoring if exists
    if (audioCleanupRef.current) {
      audioCleanupRef.current();
      audioCleanupRef.current = null;
    }

    try {
      // Create audio context for simple level detection
      const AudioContextClass = window.AudioContext || (window as typeof window & { webkitAudioContext?: new () => AudioContext }).webkitAudioContext;
      if (!AudioContextClass) {
        return;
      }
      const audioContext = new AudioContextClass();
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 128;
      analyser.smoothingTimeConstant = 0.3;
      
      const stream = new MediaStream([track]);
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);

      let silenceCount = 0;
      let isMonitoring = true;

      const checkAudio = () => {
        if (!isMonitoring) return;

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
        
        if (average > 10) {
          if (!hasHeardSpeechRef.current) {
            hasHeardSpeechRef.current = true;
            setConnectionState('speaking');
            
            if (thinkingTimeoutRef.current) {
              clearTimeout(thinkingTimeoutRef.current);
              thinkingTimeoutRef.current = null;
            }
          } else if (connectionState === 'connected' || connectionState === 'thinking') {
            setConnectionState('speaking');
          }
          silenceCount = 0;
        } else {
          // Silence detected
          if (hasHeardSpeechRef.current && connectionState === 'speaking') {
            silenceCount++;
            if (silenceCount > 15) {
              // Been silent for a while, transition to connected/thinking
              setConnectionState('connected');
              
              thinkingTimeoutRef.current = setTimeout(() => {
                // Keep showing thinking indicator
              }, 2000);
            }
          }
        }

        requestAnimationFrame(checkAudio);
      };

      // Start checking after a short delay to let audio initialize
      setTimeout(() => {
        requestAnimationFrame(checkAudio);
      }, 500);

      // Store cleanup function
      audioCleanupRef.current = () => {
        isMonitoring = false;
        audioContext.close();
        source.disconnect();
      };
    } catch (error) {
      console.error('Error setting up audio monitoring:', error);
      // Fallback: show connected after delay
      setTimeout(() => {
        if (!hasHeardSpeechRef.current) {
          setConnectionState('connected');
        }
      }, 2000);
    }
  };


  const toggleMute = () => {
    if (localParticipant.localParticipant) {
      localParticipant.localParticipant.setMicrophoneEnabled(!isMuted);
      setIsMuted(!isMuted);
    }
  };

  const getConnectionStatus = () => {
    switch (connectionState) {
      case 'connecting':
        return {
          text: 'Connecting...',
          color: 'yellow',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          textColor: 'text-yellow-800',
          dotColor: 'bg-yellow-500'
        };
      case 'thinking':
        return {
          text: 'AI is thinking...',
          color: 'blue',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          textColor: 'text-blue-800',
          dotColor: 'bg-blue-500'
        };
      case 'speaking':
        return {
          text: 'AI is speaking',
          color: 'green',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          textColor: 'text-green-800',
          dotColor: 'bg-green-500'
        };
      case 'connected':
        return {
          text: 'Connected',
          color: 'green',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          textColor: 'text-green-800',
          dotColor: 'bg-green-500'
        };
      default:
        return {
          text: 'Connected',
          color: 'green',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          textColor: 'text-green-800',
          dotColor: 'bg-green-500'
        };
    }
  };

  const status = getConnectionStatus();

  return (
    <div className="space-y-4">
      {/* Status Bar */}
      <div className={`p-4 ${status.bgColor} rounded-lg border ${status.borderColor} transition-all duration-300`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 ${status.dotColor} rounded-full ${
              connectionState === 'thinking' ? 'animate-pulse' : 
              connectionState === 'speaking' ? 'animate-pulse' : 
              connectionState === 'connecting' ? 'animate-pulse' : ''
            }`}></div>
            <div className="flex flex-col">
              <span className={`text-sm font-semibold ${status.textColor}`}>
                {status.text}
              </span>
              {currentAgent && connectionState !== 'connecting' && (
                <span className="text-xs text-gray-600 mt-0.5">
                  {getAgentDisplayName(currentAgent)}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onDisconnect}
            className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-semibold"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Disconnect
          </button>
        </div>
      </div>

      {/* Main Voice Interface */}
      <div className="p-6 bg-gray-50 rounded-lg border border-gray-200 text-center">
        <div className="mb-4">
          <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full mb-4 transition-all duration-300 ${
            connectionState === 'speaking' ? 'bg-green-100 scale-110 shadow-lg' :
            connectionState === 'thinking' ? 'bg-blue-100 animate-pulse' :
            connectionState === 'connecting' ? 'bg-yellow-100 animate-pulse' :
            'bg-gray-100'
          }`}>
            <PhoneIcon className={`w-10 h-10 transition-colors duration-300 ${
              connectionState === 'speaking' ? 'text-green-600' :
              connectionState === 'thinking' ? 'text-blue-600' :
              connectionState === 'connecting' ? 'text-yellow-600' :
              'text-gray-600'
            }`} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {connectionState === 'speaking' ? 'AI is Speaking' :
             connectionState === 'thinking' ? 'AI is Thinking' :
             connectionState === 'connecting' ? 'Connecting...' :
             'Voice Conversation Active'}
          </h3>
          <p className="text-sm text-gray-600">
            {connectionState === 'speaking' ? 'Listen to the AI response' :
             connectionState === 'thinking' ? 'The AI is processing your request...' :
             connectionState === 'connecting' ? 'Establishing connection...' :
             'Speak naturally to continue the conversation'}
          </p>
        </div>

        <button
          onClick={toggleMute}
          className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 ${
            isMuted
              ? 'bg-red-600 text-white hover:bg-red-700 shadow-md'
              : 'bg-green-600 text-white hover:bg-green-700 shadow-md'
          }`}
        >
          {isMuted ? 'Unmute Microphone' : 'Mute Microphone'}
        </button>
      </div>

      {/* Example Commands */}
      <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
        <p className="text-sm text-blue-800 mb-2">
          <strong>Example commands:</strong>
        </p>
        <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
          {currentAgent ? (
            <>
              <li>&quot;I need to schedule an appointment&quot;</li>
              <li>&quot;I have a question about my bill&quot;</li>
              <li>&quot;I need a prescription refill&quot;</li>
              <li>&quot;I want to check my insurance coverage&quot;</li>
            </>
          ) : (
            <>
              <li>&quot;What&apos;s on the menu?&quot;</li>
              <li>&quot;I&apos;d like a Caesar Salad&quot;</li>
              <li>&quot;What&apos;s in my current order?&quot;</li>
              <li>&quot;I&apos;m ready to place my order&quot;</li>
            </>
          )}
        </ul>
      </div>
    </div>
  );
}
