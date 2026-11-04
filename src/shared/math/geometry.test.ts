import { describe, expect, it } from 'vitest';
import {
  fitToBox, pointInPolygon, pointSegment, polygonArea, resampleClosed,
  ringDistance, segmentsCross, segmentSegmentDistance, wrapIndex,
} from './geometry';
import { reflect } from './vec';
import { createRng } from './random';

const square = [{ x: 0, y: 0 }, { x: 10, y: 0 }, { x: 10, y: 10 }, { x: 0, y: 10 }];

describe('geometry', () => {
  it('computes signed polygon area', () => {
    expect(polygonArea(square)).toBe(100);
    expect(polygonArea([...square].reverse())).toBe(-100);
  });

  it('tests points inside a polygon', () => {
    expect(pointInPolygon(5, 5, square)).toBe(true);
    expect(pointInPolygon(15, 5, square)).toBe(false);
  });

  it('finds the closest point on a segment', () => {
    const hit = pointSegment(5, 3, { x: 0, y: 0 }, { x: 10, y: 0 });
    expect(hit).toEqual({ d: 3, t: 0.5, qx: 5, qy: 0 });
    expect(pointSegment(-4, 3, { x: 0, y: 0 }, { x: 10, y: 0 }).d).toBe(5);
  });

  it('detects crossing segments', () => {
    expect(segmentsCross({ x: 0, y: 0 }, { x: 10, y: 10 }, { x: 0, y: 10 }, { x: 10, y: 0 })).toBe(true);
    expect(segmentsCross({ x: 0, y: 0 }, { x: 10, y: 0 }, { x: 0, y: 5 }, { x: 10, y: 5 })).toBe(false);
    expect(segmentSegmentDistance({ x: 0, y: 0 }, { x: 10, y: 0 }, { x: 0, y: 5 }, { x: 10, y: 5 })).toBe(5);
  });

  it('resamples a closed outline to evenly spaced points', () => {
    const r = resampleClosed(square, 8);
    expect(r).toHaveLength(8);
    for (let i = 0; i < 8; i++) {
      const a = r[i]!, b = r[(i + 1) % 8]!;
      expect(Math.hypot(b.x - a.x, b.y - a.y)).toBeCloseTo(5);
    }
  });

  it('fits points into a box', () => {
    const f = fitToBox(square, 100, 50, 50);
    expect(f[0]).toEqual({ x: 0, y: 0 });
    expect(f[2]).toEqual({ x: 100, y: 100 });
  });

  it('measures distance around a ring', () => {
    expect(ringDistance(1, 399, 400)).toBe(2);
    expect(wrapIndex(-1, 400)).toBe(399);
  });

  it('reflects velocity with equal angles in and out', () => {
    expect(reflect({ x: 3, y: -4 }, { x: 0, y: 1 })).toEqual({ x: 3, y: 4 });
  });
});

describe('random', () => {
  it('is reproducible from a seed', () => {
    const a = createRng(42), b = createRng(42);
    const seqA = Array.from({ length: 5 }, () => a.next());
    expect(Array.from({ length: 5 }, () => b.next())).toEqual(seqA);
    expect(seqA.every((v) => v >= 0 && v < 1)).toBe(true);
  });
});
