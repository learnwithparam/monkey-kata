'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { PhoneIcon } from '@heroicons/react/24/outline';
import { Room, RoomEvent } from 'livekit-client';
import { RoomAudioRenderer, RoomContext } from '@livekit/components-react';
import SubmitButton from '@/components/demos/SubmitButton';
import AlertMessage from '@/components/demos/AlertMessage';
import VoiceInterface from '@/components/demos/VoiceInterface';

interface ConnectionDetails {
  server_url: string;
  room_name: string;
  participant_name: string;
  participant_token: string;
}

export default function RestaurantBookingPage() {
  const [connectionDetails, setConnectionDetails] = useState<ConnectionDetails | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState('');
  const [participantName, setParticipantName] = useState('');
  const room = useMemo(() => new Room(), []);

  useEffect(() => {
    const onDisconnected = () => {
      setIsConnected(false);
      setConnectionDetails(null);
    };
    
    const onMediaDevicesError = (err: Error) => {
      setError(`Media device error: ${err.message}`);
    };

    room.on(RoomEvent.Disconnected, onDisconnected);
    room.on(RoomEvent.MediaDevicesError, onMediaDevicesError);

    return () => {
      room.off(RoomEvent.Disconnected, onDisconnected);
      room.off(RoomEvent.MediaDevicesError, onMediaDevicesError);
      room.disconnect();
    };
  }, [room]);

  useEffect(() => {
    if (isConnected && connectionDetails && room.state === 'disconnected') {
      room.localParticipant.setMicrophoneEnabled(true);
      room.connect(connectionDetails.server_url, connectionDetails.participant_token)
        .then(() => {
          setIsConnected(true);
        })
        .catch((err) => {
          setError(`Connection failed: ${err.message}`);
          setIsConnected(false);
        });
    }
  }, [isConnected, connectionDetails, room]);

  const connectToVoiceAgent = async () => {
    if (!participantName.trim()) {
      setError('Please enter your name');
      return;
    }

    setIsConnecting(true);
    setError('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/restaurant-booking/connection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ participant_name: participantName }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const details: ConnectionDetails = await response.json();
      setConnectionDetails(details);
      setIsConnected(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect to voice agent');
      setIsConnected(false);
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnect = () => {
    room.disconnect();
    setIsConnected(false);
    setConnectionDetails(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-200 mb-6">
            <PhoneIcon className="w-8 h-8 text-gray-600" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Restaurant Booking Voice AI
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-6">
            Speak naturally to place your order, ask about the menu, and complete your booking.
          </p>
          <Link
            href="/challenges/restaurant-booking"
            className="bg-white text-gray-900 font-semibold py-3 px-6 rounded-lg border border-gray-200 hover:border-gray-300 transition-all duration-200 shadow-sm hover:shadow-md inline-block"
          >
            View Learning Challenges
          </Link>
        </div>

        {/* Main Content */}
        <div className="card p-6 sm:p-8">
          {!isConnected ? (
            <div className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="participant_name" className="block text-sm font-semibold text-gray-700">
                  Your Name
                </label>
                <input
                  type="text"
                  id="participant_name"
                  value={participantName}
                  onChange={(e) => setParticipantName(e.target.value)}
                  placeholder="Enter your name (required)"
                  required
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-gray-900 placeholder-gray-400 bg-white hover:border-gray-300"
                  disabled={isConnecting}
                />
              </div>

              <SubmitButton
                isLoading={isConnecting}
                onClick={connectToVoiceAgent}
                disabled={!participantName.trim() || participantName.trim().length < 2 || isConnecting}
              >
                <span className="flex items-center justify-center">
                  <PhoneIcon className="w-5 h-5 mr-2" />
                  Connect to Voice Agent
                </span>
              </SubmitButton>

              {error && (
                <AlertMessage
                  type="error"
                  message={error}
                />
              )}
            </div>
          ) : (
            <RoomContext.Provider value={room}>
              <RoomAudioRenderer />
              <VoiceInterface 
                onDisconnect={disconnect}
                examples={[
                  "What's on the menu?",
                  "I'd like a Caesar Salad",
                  "What's in my current order?",
                  "I'm ready to place my order"
                ]}
              />
            </RoomContext.Provider>
          )}
        </div>
      </div>
    </div>
  );
}

