export function ScenicIllustration() {
  return (
    <svg
      viewBox="0 0 420 340"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ width: '100%', height: '100%', display: 'block' }}
      aria-hidden="true"
    >
      {/* Peach background block */}
      <rect x="20" y="20" width="380" height="300" rx="18" fill="#fde5da" />

      {/* Glowing Golden Sun */}
      <circle cx="285" cy="85" r="28" fill="#f97316" />

      {/* Soft decorative cloud line-art */}
      <path
        d="M75 125 C82 110 102 110 112 120 C120 115 136 117 138 126 C144 126 148 132 144 137 C140 140 80 140 75 135 Z"
        fill="#ffffff"
        opacity="0.85"
      />
      <path
        d="M60 98 C72 88 95 90 98 102"
        stroke="#c7a79a"
        strokeWidth="1.5"
        strokeLinecap="round"
      />

      {/* Snow hill back layer */}
      <path
        d="M20 265 C120 240 220 270 400 225 L400 320 L20 320 Z"
        fill="#f7faf8"
      />

      {/* Orange Autumn Tree */}
      <polygon points="120,145 106,205 134,205" fill="#e87a24" />
      <polygon points="120,180 102,215 138,215" fill="#f97316" />
      <rect x="118" y="215" width="4" height="28" fill="#a0522d" />

      {/* White wireframe tree */}
      <line x1="175" y1="145" x2="175" y2="245" stroke="#ffffff" strokeWidth="2" />
      <line x1="175" y1="165" x2="160" y2="185" stroke="#ffffff" strokeWidth="1.5" />
      <line x1="175" y1="165" x2="190" y2="185" stroke="#ffffff" strokeWidth="1.5" />
      <line x1="175" y1="190" x2="155" y2="215" stroke="#ffffff" strokeWidth="1.5" />
      <line x1="175" y1="190" x2="195" y2="215" stroke="#ffffff" strokeWidth="1.5" />

      {/* Cozy Navy Cabin */}
      {/* Chimney */}
      <rect x="235" y="175" width="16" height="22" fill="#1e293b" rx="2" />
      <path
        d="M243 173 C240 165 252 160 248 153 C245 147 255 143 262 140"
        stroke="#8a9ba8"
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
      />

      {/* Cabin Main Body */}
      <polygon points="215,215 270,180 315,205 315,275 215,275" fill="#1e293b" />
      <polygon points="215,215 248,195 248,275 215,275" fill="#d96b27" />

      {/* Snow on Cabin Roof */}
      <path
        d="M205 219 L268 177 C271 175 275 177 278 179 L324 205 C326 206 324 210 320 210 L272 185 L212 223 Z"
        fill="#ffffff"
      />

      {/* Cozy window with soft teal glow */}
      <rect x="265" y="220" width="14" height="18" fill="#7dd3fc" rx="2" />

      {/* Front Snow hill / Foreground */}
      <path
        d="M20 285 C140 270 240 290 400 260 L400 320 L20 320 Z"
        fill="#ffffff"
      />
      <path
        d="M100 283 C135 273 170 285 190 295 L190 320 L100 320 Z"
        fill="#334155"
        opacity="0.8"
      />

      {/* Teal Evergreen Spruce Trees */}
      <polygon points="345,160 330,210 360,210" fill="#2a9d8f" />
      <polygon points="345,195 324,240 366,240" fill="#228176" />
      <polygon points="345,225 320,265 370,265" fill="#1e7067" />
      <rect x="343" y="265" width="4" height="18" fill="#134e48" />

      {/* Foreground small hill curve */}
      <path
        d="M250 280 C285 290 350 300 400 285 L400 320 L250 320 Z"
        fill="#93c5be"
        opacity="0.6"
      />
    </svg>
  )
}
