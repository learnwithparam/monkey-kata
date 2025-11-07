import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Travel Customer Support Assistant | AI Bootcamp Demos",
  description: "Your AI-powered travel support assistant (like Booking.com) that helps with booking lookups, hotel reservations, flight status, and taxi bookings.",
};

export default function TravelSupportLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}

