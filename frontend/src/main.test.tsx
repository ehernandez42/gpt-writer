import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import { describe, expect, it } from 'vitest'

describe('frontend entry styling', () => {
  it('imports a stylesheet from the app entrypoint', () => {
    const mainSource = readFileSync(resolve(__dirname, './main.tsx'), 'utf-8')

    expect(mainSource).toMatch(/import\s+['\"].+\.css['\"]/)
  })
})
