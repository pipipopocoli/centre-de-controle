import type { LoadedAssetData } from '../layout/furnitureCatalog.js'
import type { SpriteData } from '../types.js'
import { buildDynamicCatalog } from '../layout/furnitureCatalog.js'
import { setFloorColorizeEnabled, setFloorSprites } from '../floorTiles.js'

const TILE = 16
const DONARG_ROOT = '/local-assets/donarg'

type TileRect = {
  col: number
  row: number
  widthTiles: number
  heightTiles: number
}

type AtlasKey = 'office16' | 'office1' | 'office2'

type ThemeCatalogEntry = {
  atlas: AtlasKey
  id: string
  label: string
  category: string
  footprintW: number
  footprintH: number
  isDesk: boolean
  rect: TileRect
  groupId?: string
  orientation?: string
  state?: string
  canPlaceOnSurfaces?: boolean
  backgroundTiles?: number
  canPlaceOnWalls?: boolean
}

type ThemeCatalogPayload = {
  version: number
  entries: ThemeCatalogEntry[]
}

function encoded(path: string): string {
  return encodeURI(path)
}

function buildAssetCandidates(file: string): string[] {
  const base = (import.meta.env.BASE_URL ?? '/').replace(/\/+$/, '')
  return [
    encoded(`${DONARG_ROOT}/${file}`),
    encoded(`${base}${DONARG_ROOT}/${file}`),
    encoded(`local-assets/donarg/${file}`),
  ]
}

const DONARG_ATLAS_NO_SHADOW = buildAssetCandidates('Office Tileset All 16x16 no shadow.png')
const DONARG_ATLAS_SHADOW = buildAssetCandidates('Office Tileset All 16x16.png')
const DONARG_FLOORS_ATLAS = buildAssetCandidates('A2 Office Floors.png')
const DONARG_OFFICE1_ATLAS = buildAssetCandidates('B-C-D-E Office 1 No Shadows.png')
const DONARG_OFFICE2_ATLAS = buildAssetCandidates('B-C-D-E Office 2 No Shadows.png')
const DONARG_CATALOG = buildAssetCandidates('furniture-catalog.json')

const FLOOR_COORDS_A2: Array<{ col: number; row: number }> = [
  { col: 0, row: 6 },
  { col: 2, row: 6 },
  { col: 4, row: 6 },
  { col: 6, row: 6 },
  { col: 8, row: 6 },
  { col: 10, row: 6 },
  { col: 12, row: 6 },
]

const FALLBACK_RECTS: ThemeCatalogEntry[] = [
  { atlas: 'office16', id: 'desk', label: 'Desk', category: 'desks', footprintW: 2, footprintH: 2, isDesk: true, rect: { col: 0, row: 0, widthTiles: 2, heightTiles: 2 } },
  { atlas: 'office16', id: 'chair', label: 'Chair', category: 'chairs', footprintW: 1, footprintH: 1, isDesk: false, rect: { col: 5, row: 13, widthTiles: 1, heightTiles: 1 } },
  { atlas: 'office16', id: 'bookshelf', label: 'Bookshelf', category: 'storage', footprintW: 1, footprintH: 2, isDesk: false, rect: { col: 10, row: 5, widthTiles: 1, heightTiles: 2 } },
  { atlas: 'office16', id: 'plant', label: 'Plant', category: 'decor', footprintW: 1, footprintH: 1, isDesk: false, rect: { col: 3, row: 27, widthTiles: 1, heightTiles: 2 } },
  { atlas: 'office16', id: 'cooler', label: 'Cooler', category: 'misc', footprintW: 1, footprintH: 1, isDesk: false, rect: { col: 8, row: 14, widthTiles: 1, heightTiles: 2 } },
  { atlas: 'office16', id: 'whiteboard', label: 'Whiteboard', category: 'decor', footprintW: 2, footprintH: 1, isDesk: false, rect: { col: 0, row: 26, widthTiles: 2, heightTiles: 1 } },
  { atlas: 'office16', id: 'pc', label: 'PC', category: 'electronics', footprintW: 1, footprintH: 1, isDesk: false, rect: { col: 10, row: 19, widthTiles: 1, heightTiles: 1 } },
  { atlas: 'office16', id: 'lamp', label: 'Lamp', category: 'decor', footprintW: 1, footprintH: 1, isDesk: false, rect: { col: 8, row: 18, widthTiles: 1, heightTiles: 1 } },
  { atlas: 'office16', id: 'desk-modern-gray', label: 'Desk Gray', category: 'desks', footprintW: 2, footprintH: 2, isDesk: true, rect: { col: 0, row: 2, widthTiles: 2, heightTiles: 2 } },
  { atlas: 'office16', id: 'desk-modern-light', label: 'Desk Light', category: 'desks', footprintW: 2, footprintH: 2, isDesk: true, rect: { col: 2, row: 2, widthTiles: 2, heightTiles: 2 } },
  { atlas: 'office16', id: 'desk-long-wood', label: 'Desk Long', category: 'desks', footprintW: 3, footprintH: 2, isDesk: true, rect: { col: 5, row: 0, widthTiles: 3, heightTiles: 2 } },
  { atlas: 'office16', id: 'desk-long-white', label: 'Desk White', category: 'desks', footprintW: 3, footprintH: 2, isDesk: true, rect: { col: 8, row: 0, widthTiles: 3, heightTiles: 2 } },
  { atlas: 'office16', id: 'table-meeting', label: 'Meeting Table', category: 'desks', footprintW: 4, footprintH: 2, isDesk: true, rect: { col: 0, row: 7, widthTiles: 4, heightTiles: 2 } },
  { atlas: 'office16', id: 'sofa-gray', label: 'Sofa Gray', category: 'misc', footprintW: 3, footprintH: 2, isDesk: false, rect: { col: 7, row: 3, widthTiles: 3, heightTiles: 2 } },
  { atlas: 'office16', id: 'bookshelf-wood', label: 'Shelf Wood', category: 'storage', footprintW: 1, footprintH: 2, isDesk: false, rect: { col: 8, row: 5, widthTiles: 1, heightTiles: 2 } },
  { atlas: 'office16', id: 'bookshelf-wide', label: 'Shelf Wide', category: 'storage', footprintW: 2, footprintH: 2, isDesk: false, rect: { col: 11, row: 5, widthTiles: 2, heightTiles: 2 } },
  { atlas: 'office16', id: 'cabinet-double', label: 'Cabinet', category: 'storage', footprintW: 2, footprintH: 2, isDesk: false, rect: { col: 9, row: 14, widthTiles: 2, heightTiles: 2 } },
  { atlas: 'office16', id: 'locker', label: 'Locker', category: 'storage', footprintW: 1, footprintH: 2, isDesk: false, rect: { col: 11, row: 14, widthTiles: 1, heightTiles: 2 } },
  { atlas: 'office16', id: 'vending-machine', label: 'Vending', category: 'electronics', footprintW: 1, footprintH: 2, isDesk: false, rect: { col: 13, row: 14, widthTiles: 1, heightTiles: 2 } },
  { atlas: 'office16', id: 'clock', label: 'Clock', category: 'decor', footprintW: 1, footprintH: 1, isDesk: false, rect: { col: 0, row: 22, widthTiles: 1, heightTiles: 1 } },
  { atlas: 'office16', id: 'frame-landscape', label: 'Frame', category: 'decor', footprintW: 2, footprintH: 1, isDesk: false, rect: { col: 0, row: 24, widthTiles: 2, heightTiles: 1 } },
  { atlas: 'office16', id: 'frame-portrait', label: 'Portrait', category: 'decor', footprintW: 1, footprintH: 1, isDesk: false, rect: { col: 3, row: 24, widthTiles: 1, heightTiles: 1 } },
  { atlas: 'office16', id: 'plant-tall', label: 'Plant Tall', category: 'decor', footprintW: 1, footprintH: 1, isDesk: false, rect: { col: 5, row: 27, widthTiles: 1, heightTiles: 2 } },
]

let loadPromise: Promise<boolean> | null = null

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error(`failed to load image: ${src}`))
    image.src = src
  })
}

async function loadFirstAvailableImage(sources: string[]): Promise<HTMLImageElement> {
  let lastError: unknown = null
  for (const src of sources) {
    try {
      return await loadImage(src)
    } catch (error) {
      lastError = error
    }
  }
  throw lastError ?? new Error('no image source available')
}

async function loadCatalogJson(): Promise<ThemeCatalogPayload | null> {
  for (const src of DONARG_CATALOG) {
    try {
      const response = await fetch(src)
      if (!response.ok) {
        continue
      }
      const payload = (await response.json()) as Partial<ThemeCatalogPayload>
      if (!payload || !Array.isArray(payload.entries)) {
        continue
      }
      return {
        version: typeof payload.version === 'number' ? payload.version : 1,
        entries: payload.entries.filter((entry): entry is ThemeCatalogEntry => {
          if (!entry || typeof entry !== 'object') {
            return false
          }
          const atlas = entry.atlas
          const rect = entry.rect
          return (
            (atlas === 'office16' || atlas === 'office1' || atlas === 'office2') &&
            typeof entry.id === 'string' &&
            typeof entry.label === 'string' &&
            typeof entry.category === 'string' &&
            typeof entry.footprintW === 'number' &&
            typeof entry.footprintH === 'number' &&
            typeof entry.isDesk === 'boolean' &&
            rect !== undefined &&
            typeof rect.col === 'number' &&
            typeof rect.row === 'number' &&
            typeof rect.widthTiles === 'number' &&
            typeof rect.heightTiles === 'number'
          )
        }),
      }
    } catch {
      // try next candidate
    }
  }
  return null
}

function makeContext(image: HTMLImageElement): CanvasRenderingContext2D {
  const canvas = document.createElement('canvas')
  canvas.width = image.width
  canvas.height = image.height
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('failed to create 2d context')
  }
  ctx.imageSmoothingEnabled = false
  ctx.drawImage(image, 0, 0)
  return ctx
}

function extractSprite(ctx: CanvasRenderingContext2D, x: number, y: number, width: number, height: number): SpriteData {
  const imageData = ctx.getImageData(x, y, width, height).data
  const sprite: SpriteData = []
  for (let row = 0; row < height; row++) {
    const outRow: string[] = []
    for (let col = 0; col < width; col++) {
      const i = (row * width + col) * 4
      const r = imageData[i]
      const g = imageData[i + 1]
      const b = imageData[i + 2]
      const a = imageData[i + 3]
      if (a < 16 || (r === 0 && g === 0 && b === 0)) {
        outRow.push('')
        continue
      }
      outRow.push(`#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`)
    }
    sprite.push(outRow)
  }
  return sprite
}

function extractTileRect(ctx: CanvasRenderingContext2D, rect: TileRect): SpriteData {
  return extractSprite(
    ctx,
    rect.col * TILE,
    rect.row * TILE,
    rect.widthTiles * TILE,
    rect.heightTiles * TILE,
  )
}

function hasVisiblePixels(sprite: SpriteData): boolean {
  return sprite.some((row) => row.some((pixel) => pixel !== ''))
}

export function loadDonargTheme(): Promise<boolean> {
  if (loadPromise) {
    return loadPromise
  }

  loadPromise = (async () => {
    try {
      const [all16Image, floorsImage, office1Image, office2Image, catalogJson] = await Promise.all([
        loadFirstAvailableImage([...DONARG_ATLAS_NO_SHADOW, ...DONARG_ATLAS_SHADOW]),
        loadFirstAvailableImage(DONARG_FLOORS_ATLAS),
        loadFirstAvailableImage(DONARG_OFFICE1_ATLAS),
        loadFirstAvailableImage(DONARG_OFFICE2_ATLAS),
        loadCatalogJson(),
      ])

      const all16Ctx = makeContext(all16Image)
      const floorsCtx = makeContext(floorsImage)
      const office1Ctx = makeContext(office1Image)
      const office2Ctx = makeContext(office2Image)

      const floorSprites = FLOOR_COORDS_A2
        .map(({ col, row }) => extractTileRect(floorsCtx, { col, row, widthTiles: 1, heightTiles: 1 }))
        .filter(hasVisiblePixels)
      if (floorSprites.length > 0) {
        setFloorSprites(floorSprites)
        setFloorColorizeEnabled(false)
      }

      const atlasContexts: Record<AtlasKey, CanvasRenderingContext2D> = {
        office16: all16Ctx,
        office1: office1Ctx,
        office2: office2Ctx,
      }

      const sourceEntries = catalogJson?.entries.length ? catalogJson.entries : FALLBACK_RECTS
      const sprites: Record<string, SpriteData> = {}
      const catalog = sourceEntries
        .map((entry) => {
          const atlas = atlasContexts[entry.atlas]
          if (!atlas) {
            return null
          }
          const sprite = extractTileRect(atlas, entry.rect)
          if (!hasVisiblePixels(sprite)) {
            return null
          }
          sprites[entry.id] = sprite
          return {
            id: entry.id,
            label: entry.label,
            category: entry.category,
            width: entry.rect.widthTiles * TILE,
            height: entry.rect.heightTiles * TILE,
            footprintW: entry.footprintW,
            footprintH: entry.footprintH,
            isDesk: entry.isDesk,
            ...(entry.groupId ? { groupId: entry.groupId } : {}),
            ...(entry.orientation ? { orientation: entry.orientation } : {}),
            ...(entry.state ? { state: entry.state } : {}),
            ...(entry.canPlaceOnSurfaces ? { canPlaceOnSurfaces: true } : {}),
            ...(entry.backgroundTiles ? { backgroundTiles: entry.backgroundTiles } : {}),
            ...(entry.canPlaceOnWalls ? { canPlaceOnWalls: true } : {}),
          }
        })
        .filter((entry) => entry !== null)

      const loadedAssets: LoadedAssetData = {
        catalog,
        sprites,
      }

      const catalogBuilt = buildDynamicCatalog(loadedAssets)
      if (catalogBuilt) {
        const sourceLabel = catalogJson?.entries.length ? 'furniture-catalog.json' : 'fallback'
        console.info(`[donarg-theme] active: ${sourceLabel}, entries=${catalog.length}`)
      }
      return catalogBuilt
    } catch (error) {
      console.info('[donarg-theme] skipped', error)
      return false
    }
  })()

  return loadPromise
}
