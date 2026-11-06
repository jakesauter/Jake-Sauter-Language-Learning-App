  /* topic icons: one-color line drawings, so every section has a picture to anchor it (dual coding) */

  const ICON_PATHS = {
    flag: "M5 21V4M5 4h11l-2.5 4L16 12H5",
    chat: "M4 5h16v10H10l-5 4v-4H4z",
    bolt: "M13 2 5 13h6l-1 9 8-11h-6z",
    smile: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM8.5 14.5c1.8 2.2 5.2 2.2 7 0M9 9.5h.01M15 9.5h.01",
    pair: "M8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM16 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM2.5 20c.6-3.4 2.8-5.5 5.5-5.5s4.9 2.1 5.5 5.5M10.5 20c.6-3.4 2.8-5.5 5.5-5.5s4.9 2.1 5.5 5.5",
    family: "M7 9a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM17 9a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zM12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM2.5 19c.4-3.3 2.2-5.5 4.5-5.5 1.3 0 2.3.6 3 1.6M21.5 19c-.4-3.3-2.2-5.5-4.5-5.5-1.3 0-2.3.6-3 1.6M8.5 21c.4-2.5 1.8-4 3.5-4s3.1 1.5 3.5 4",
    door: "M6 21V3h12v18M3 21h18M14 12h.01",
    bowl: "M3 11h18c0 5-4 8.5-9 8.5S3 16 3 11zM9 19.5 8 21h8l-1-1.5M14 3l5 6M17 3l3 5",
    bubbles: "M3 4h11v7H7l-4 3V4zM10 14v2h7l4 3v-9h-4",
    calendar: "M4 6h16v14H4zM4 10h16M8 3v5M16 3v5",
    house: "M3 11 12 4l9 7M5 10v10h14V10M10 20v-5h4v5",
    pot: "M4 10h16v6a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4zM2 10h20M9 7c0-2 2-2 2-4M14 7c0-2 2-2 2-4",
    gift: "M4 10h16v10H4zM3 7h18v3H3zM12 7v13M12 7c-2-4-6-4-6-1.5S9 7 12 7zM12 7c2-4 6-4 6-1.5S15 7 12 7z",
    car: "M3 16v-4l2-5h14l2 5v4zM3 16v2h3v-2M18 16v2h3v-2M7 13h.01M17 13h.01",
    plane: "M2 13l7-1 4-8h2l-2 8 6 .5 2-2.5h1.5l-1 4 1 4H21l-2-2.5L13 15l2 8h-2l-4-8-7-1z",
    weather: "M7 18h10a4 4 0 0 0 .5-8A5.5 5.5 0 0 0 7 9.5 4.3 4.3 0 0 0 7 18zM16 3v2M20.5 5l-1.5 1.5M22 10h-2",
    case: "M3 8h18v12H3zM8 8V5h8v3M3 13h18",
    book: "M4 4h6a3 3 0 0 1 2 1 3 3 0 0 1 2-1h6v15h-6a2 2 0 0 0-2 2 2 2 0 0 0-2-2H4zM12 5v16",
    star: "M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z",
    waves: "M2 9c2.5-2 5-2 7.5 0s5 2 7.5 0 3.5-1.5 5 0M2 15c2.5-2 5-2 7.5 0s5 2 7.5 0 3.5-1.5 5 0",
    bike: "M6 18a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM18 18a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM6 14.5l4-7h5l3 7M10 7.5h-2M12 14.5l3-7",
    bag: "M5 8h14l-1 13H6zM9 8V6a3 3 0 0 1 6 0v2",
    paw: "M12 20c-3 0-5-1.5-5-3.5S9.5 12 12 12s5 2.5 5 4.5-2 3.5-5 3.5zM6 11a1.8 2.2 0 1 0 0-.1zM9.5 7a1.8 2.2 0 1 0 0-.1zM14.5 7a1.8 2.2 0 1 0 0-.1zM18 11a1.8 2.2 0 1 0 0-.1z",
    health: "M12 20s-7.5-4.5-7.5-10A4.5 4.5 0 0 1 12 7a4.5 4.5 0 0 1 7.5 3c0 5.5-7.5 10-7.5 10zM8 12h2.5l1-2 2 4 1-2H16",
    hands: "M3 12l4-4 4 3 3-3 7 6-5 5-4-3-3 2zM11 11l-3 3",
    bulb: "M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z",
    sparkle: "M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18",
    heart: "M12 20s-8-4.8-8-10.5A4.5 4.5 0 0 1 12 7a4.5 4.5 0 0 1 8 2.5C20 15.2 12 20 12 20z",
    laugh: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM7.5 13h9a4.5 4.5 0 0 1-9 0zM8 9l2 1-2 1M16 9l-2 1 2 1",
    wave: "M8 13V6a1.5 1.5 0 0 1 3 0v5M11 11V4.5a1.5 1.5 0 0 1 3 0V11M14 11V6a1.5 1.5 0 0 1 3 0v8a6 6 0 0 1-6 6h-.5a6 6 0 0 1-4.8-2.4L3.5 14a1.5 1.5 0 0 1 2.3-1.9L8 14.5M19.5 3.5c1 1 1.5 2 1.5 3.5",
    brain: "M9 4a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 2 5 3 3 0 0 0 6 1V5a2.5 2.5 0 0 0-3-1zM15 4a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-2 5 3 3 0 0 1-6 1",
    cards: "M7 4h11a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zM3 7v11a2 2 0 0 0 2 2",
    ear: "M7 9a5 5 0 0 1 10 0c0 3-3 4-3 7a3 3 0 0 1-5.5 1.5M10 9a2 2 0 0 1 4 0c0 1.5-2 2-2 3.5",
    mic: "M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3zM5 11a7 7 0 0 0 14 0M12 18v3",
    tones: "M3 6h4M3 12l4-4M3 17l4 1M10 7c2 0 2 9 4 9s2-6 4-6 2 3 3 3",
  };

  const CAT_ICON = {
    "Start Here": "flag", "Talking About the Day": "chat", "Quick Patterns": "bolt", "Greetings": "smile", "Getting to know you": "pair", "Family": "family",
    "Visiting": "door", "Meals": "bowl", "Small Talk": "bubbles", "Plans": "calendar", "Around the House": "house", "Cooking Together": "pot",
    "Family Events": "gift", "Road Trip": "car", "Travel": "plane", "Weather": "weather", "Work": "case", "School": "book", "Hobbies": "star",
    "Swimming": "waves", "Running & Biking": "bike", "Shopping": "bag", "Pets": "paw", "Health": "health", "Helping Out": "hands", "Learning": "bulb",
    "Holidays": "sparkle", "Feelings": "heart", "Joking Around": "laugh", "Goodbyes": "wave",
  };

  function icon(name, cls = "ico") {
    const d = ICON_PATHS[name] || ICON_PATHS.chat;
    return `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true"><path d="${d}" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  }

  const catIcon = c => icon(CAT_ICON[c] || "chat");
