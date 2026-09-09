import { useEffect } from 'react'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import L from 'leaflet'
import type { Partner, ScoredPartner } from '../../types'

const API_URL = import.meta.env.VITE_MAP_TILE_URL || 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

const defaultIcon = L.divIcon({
  className: '',
  html: `<div style="background:#0b2545;color:#fff;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;border:3px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.35)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg></div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 28],
})

const userIcon = L.divIcon({
  className: '',
  html: `<div style="background:#e11d48;color:#fff;border-radius:50%;width:18px;height:18px;border:3px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.35)"></div>`,
  iconSize: [18, 18],
  iconAnchor: [9, 9],
})

function FitView({ coords }: { coords: [number, number] | null }) {
  const map = useMap()
  useEffect(() => {
    if (coords) map.flyTo(coords, 11, { duration: 0.6 })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [coords])
  return null
}

export default function MapPanel({
  partners,
  selected,
  userCoords,
  onSelect,
}: {
  partners: (Partner | ScoredPartner)[]
  selected: number | null
  userCoords: [number, number] | null
  onSelect: (id: number) => void
}) {
  const center: [number, number] = userCoords || [23.2599, 77.4126]

  return (
    <div className="h-full w-full overflow-hidden rounded-2xl">
      <MapContainer
        center={center}
        zoom={userCoords ? 10 : 5}
        className="h-full w-full"
        scrollWheelZoom={false}
        aria-label="Partner map"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url={API_URL}
        />
        {userCoords && (
          <Marker position={userCoords} icon={userIcon}>
            <Popup>Your location</Popup>
          </Marker>
        )}
        {partners.map((p) => {
          const isSel = p.id === selected
          const color = p.status === 'accepting' ? '#059669' : p.status === 'limited' ? '#d97706' : '#dc2626'
          return (
            <Marker
              key={p.id}
              position={[p.latitude, p.longitude]}
              icon={L.divIcon({
                className: '',
                html: `<div style="background:${color};color:#fff;border-radius:50%;width:${isSel ? 34 : 28}px;height:${isSel ? 34 : 28}px;display:flex;align-items:center;justify-content:center;border:3px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4);font-size:11px;font-weight:700">${p.type}</div>`,
                iconSize: [isSel ? 34 : 28, isSel ? 34 : 28],
                iconAnchor: [isSel ? 17 : 14, isSel ? 17 : 14],
              })}
              eventHandlers={{ click: () => onSelect(p.id) }}
            >
              <Popup>
                <div className="w-48 text-sm">
                  <p className="font-bold">{p.name}</p>
                  <p className="text-xs text-slate-500">{p.city}, {p.state}</p>
                  <p className="mt-1 text-xs">{p.type} · {p.status}</p>
                </div>
              </Popup>
            </Marker>
          )
        })}
        <FitView coords={userCoords} />
      </MapContainer>
    </div>
  )
}