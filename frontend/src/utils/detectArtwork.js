/**
 * detectArtwork.js
 * Canvas-based artwork region detection.
 * Uses Sobel edge detection + projection profiles to find
 * the most "content-rich" rectangular region in a photo.
 */

function buildEdgeMap(imageData) {
  const { data, width: w, height: h } = imageData
  // Grayscale
  const g = new Uint8Array(w * h)
  for (let i = 0; i < w * h; i++) {
    g[i] = (data[i*4]*77 + data[i*4+1]*150 + data[i*4+2]*29) >> 8
  }
  // Sobel magnitude
  const e = new Uint8Array(w * h)
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const i = y * w + x
      const gx = (-g[i-w-1] - 2*g[i-1] - g[i+w-1]
                  + g[i-w+1] + 2*g[i+1] + g[i+w+1])
      const gy = (-g[i-w-1] - 2*g[i-w] - g[i-w+1]
                  + g[i+w-1] + 2*g[i+w] + g[i+w+1])
      e[i] = Math.min(255, (Math.abs(gx) + Math.abs(gy)) >> 1)
    }
  }
  return e
}

function smooth(arr, r = 3) {
  const out = new Float32Array(arr.length)
  for (let i = 0; i < arr.length; i++) {
    let s = 0, n = 0
    for (let j = Math.max(0, i-r); j <= Math.min(arr.length-1, i+r); j++) {
      s += arr[j]; n++
    }
    out[i] = s / n
  }
  return out
}

function findCropBox(edges, w, h) {
  const row = new Float32Array(h)
  const col = new Float32Array(w)
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) { row[y] += edges[y*w+x]; col[x] += edges[y*w+x] }

  const sr = smooth(row, 4)
  const sc = smooth(col, 4)
  const maxR = Math.max(...sr) || 1
  const maxC = Math.max(...sc) || 1
  const thr  = 0.07  // % of peak to consider "content"

  let t = 0, b = h-1, l = 0, r = w-1
  for (let y = 0; y < h;   y++) if (sr[y]/maxR > thr) { t = y; break }
  for (let y = h-1; y > 0; y--) if (sr[y]/maxR > thr) { b = y; break }
  for (let x = 0; x < w;   x++) if (sc[x]/maxC > thr) { l = x; break }
  for (let x = w-1; x > 0; x--) if (sc[x]/maxC > thr) { r = x; break }

  // small margin
  const mx = Math.round((r-l)*0.015)
  const my = Math.round((b-t)*0.015)
  return {
    x: Math.max(0, l-mx),
    y: Math.max(0, t-my),
    w: Math.min(w, r+mx) - Math.max(0, l-mx),
    h: Math.min(h, b+my) - Math.max(0, t-my),
  }
}

/**
 * Detect artwork region in a File/Blob image and return a cropped File.
 * Returns { file, cropped: true } if a meaningful crop was found,
 * or { file: original, cropped: false } otherwise.
 */
export async function cropToArtwork(inputFile) {
  try {
    const bitmap = await createImageBitmap(inputFile)
    const ow = bitmap.width, oh = bitmap.height

    // Work at max 500px for speed
    const WORK = 500
    const scale = Math.min(1, WORK / Math.max(ow, oh))
    const ww = Math.round(ow * scale)
    const wh = Math.round(oh * scale)

    const wc = document.createElement('canvas')
    wc.width = ww; wc.height = wh
    wc.getContext('2d').drawImage(bitmap, 0, 0, ww, wh)
    const edges = buildEdgeMap(wc.getContext('2d').getImageData(0, 0, ww, wh))
    const box   = findCropBox(edges, ww, wh)

    // Skip crop if < 10% reduction on both axes (not worth it)
    const widthShrink  = (ww - box.w) / ww
    const heightShrink = (wh - box.h) / wh
    if (widthShrink < 0.10 && heightShrink < 0.10) {
      bitmap.close?.()
      return { file: inputFile, cropped: false }
    }
    if (box.w < 80 || box.h < 80) {
      bitmap.close?.()
      return { file: inputFile, cropped: false }
    }

    // Map back to original resolution
    const sx = box.x / scale, sy = box.y / scale
    const sw = box.w / scale, sh = box.h / scale

    const out = document.createElement('canvas')
    out.width = Math.round(sw); out.height = Math.round(sh)
    out.getContext('2d').drawImage(bitmap, sx, sy, sw, sh, 0, 0, out.width, out.height)
    bitmap.close?.()

    const blob = await new Promise(res => out.toBlob(res, 'image/jpeg', 0.93))
    return {
      file: new File([blob], 'artwork.jpg', { type: 'image/jpeg' }),
      cropped: true,
      originalFile: inputFile,
    }
  } catch {
    return { file: inputFile, cropped: false }
  }
}
