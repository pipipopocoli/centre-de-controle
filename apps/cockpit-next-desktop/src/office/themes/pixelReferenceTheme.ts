import type { SpriteData } from '../types.js'
import { setWallColorizeEnabled, setWallSprites } from '../wallTiles.js'
import { setCharacterTemplates } from '../sprites/spriteData.js'
import type { LoadedCharacterData } from '../sprites/spriteData.js'

const PIXEL_REFERENCE_ROOT = '/local-assets/pixel-reference'
const CHAR_COUNT = 6
const CHAR_FRAME_WIDTH = 16
const CHAR_FRAME_HEIGHT = 32
const CHAR_FRAMES_PER_ROW = 7

const WALL_GRID_COLS = 4
const WALL_GRID_ROWS = 4
const WALL_TILE_WIDTH = 16
const WALL_TILE_HEIGHT = 32

let loadPromise: Promise<boolean> | null = null

function encoded(path: string): string {
  return encodeURI(path)
}

function buildAssetCandidates(file: string): string[] {
  const base = (import.meta.env.BASE_URL ?? '/').replace(/\/+$/, '')
  return [
    encoded(`${PIXEL_REFERENCE_ROOT}/${file}`),
    encoded(`${base}${PIXEL_REFERENCE_ROOT}/${file}`),
    encoded(`local-assets/pixel-reference/${file}`),
  ]
}

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
  for (const source of sources) {
    try {
      return await loadImage(source)
    } catch (error) {
      lastError = error
    }
  }
  throw lastError ?? new Error('no image source available')
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

function extractSprite(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
): SpriteData {
  const imageData = ctx.getImageData(x, y, width, height).data
  const sprite: SpriteData = []
  for (let row = 0; row < height; row++) {
    const outRow: string[] = []
    for (let col = 0; col < width; col++) {
      const index = (row * width + col) * 4
      const r = imageData[index]
      const g = imageData[index + 1]
      const b = imageData[index + 2]
      const a = imageData[index + 3]
      if (a < 16) {
        outRow.push('')
        continue
      }
      outRow.push(
        `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`.toUpperCase(),
      )
    }
    sprite.push(outRow)
  }
  return sprite
}

function decodeCharacterSheet(image: HTMLImageElement): LoadedCharacterData {
  if (
    image.width < CHAR_FRAME_WIDTH * CHAR_FRAMES_PER_ROW ||
    image.height < CHAR_FRAME_HEIGHT * 3
  ) {
    throw new Error(`invalid character sheet size: ${image.width}x${image.height}`)
  }

  const ctx = makeContext(image)
  const decodeRow = (rowIndex: number): SpriteData[] => {
    const frames: SpriteData[] = []
    const y = rowIndex * CHAR_FRAME_HEIGHT
    for (let frame = 0; frame < CHAR_FRAMES_PER_ROW; frame++) {
      const x = frame * CHAR_FRAME_WIDTH
      frames.push(extractSprite(ctx, x, y, CHAR_FRAME_WIDTH, CHAR_FRAME_HEIGHT))
    }
    return frames
  }

  return {
    down: decodeRow(0),
    up: decodeRow(1),
    right: decodeRow(2),
  }
}

function decodeWallAtlas(image: HTMLImageElement): SpriteData[] {
  if (
    image.width < WALL_GRID_COLS * WALL_TILE_WIDTH ||
    image.height < WALL_GRID_ROWS * WALL_TILE_HEIGHT
  ) {
    throw new Error(`invalid wall atlas size: ${image.width}x${image.height}`)
  }

  const ctx = makeContext(image)
  const sprites: SpriteData[] = []
  for (let mask = 0; mask < WALL_GRID_COLS * WALL_GRID_ROWS; mask++) {
    const col = mask % WALL_GRID_COLS
    const row = Math.floor(mask / WALL_GRID_COLS)
    sprites.push(
      extractSprite(
        ctx,
        col * WALL_TILE_WIDTH,
        row * WALL_TILE_HEIGHT,
        WALL_TILE_WIDTH,
        WALL_TILE_HEIGHT,
      ),
    )
  }
  return sprites
}

export function loadPixelReferenceTheme(): Promise<boolean> {
  if (loadPromise) {
    return loadPromise
  }

  loadPromise = (async () => {
    try {
      const characterSheets = await Promise.all(
        Array.from({ length: CHAR_COUNT }, (_, index) =>
          loadFirstAvailableImage(buildAssetCandidates(`characters/char_${index}.png`)).then(
            decodeCharacterSheet,
          ),
        ),
      )
      setCharacterTemplates(characterSheets)

      const wallsImage = await loadFirstAvailableImage(buildAssetCandidates('walls.png'))
      const wallSprites = decodeWallAtlas(wallsImage)
      setWallSprites(wallSprites)
      setWallColorizeEnabled(false)

      console.info('[pixel-reference-theme] loaded character strips and wall atlas')
      return true
    } catch (error) {
      console.info('[pixel-reference-theme] skipped', error)
      return false
    }
  })()

  return loadPromise
}
