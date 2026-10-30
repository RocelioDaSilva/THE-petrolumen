import { describe, it, expect } from 'vitest';
import { parseLASContent } from '../lasParser';

// LAS 2.0 standard layout: WELL.  PETRO-TEST-01 : WELL NAME
const sampleLAS = `~VERSION INFORMATION
 VERS.                          2.0 : CWLS LOG ASCII STANDARD -VERSION 2.0
 WRAP.                           NO : ONE LINE PER DEPTH STEP
~WELL INFORMATION
#MNEM .UNIT              DATA                       DESCRIPTION
#---- ------       ---------------------            --------------------
 STRT .M           1000.0000                        : START DEPTH
 STOP .M           1000.5000                        : STOP DEPTH
 STEP .M              0.1000                        : STEP
 NULL .              -999.25                        : NULL VALUE
 WELL .            PETRO-TEST-01:                   WELL NAME
~CURVE INFORMATION
#MNEM .UNIT        API CODES                        CURVE DESCRIPTION
#---- ------       ---------                        -----------------
 DEPT .M                                            : DEPTH
 GR   .GAPI                                         : GAMMA RAY
 RES  .OHMM                                         : RESISTIVITY
 RHOB .G/C3                                         : BULK DENSITY
 NPHI .V/V                                          : NEUTRON POROSITY
~ASCII
 1000.0000   45.2   12.5   2.45   0.18
 1000.1000   48.1   14.2   2.42   0.19
 1000.2000   52.0   16.0   2.39   0.21
 1000.3000   50.5   15.5   2.40   0.20
 1000.4000   46.8   13.0   2.44   0.18
 1000.5000   44.1   11.5   2.47   0.17
`;

describe('LAS Well Log Parser', () => {
  it('parses LAS 2.0 headers, curve names, and numeric records correctly', () => {
    const parsed = parseLASContent(sampleLAS, 'test_well.las');

    expect(parsed.wellName).toBe('PETRO-TEST-01');
    expect(parsed.points.length).toBe(6);
    expect(parsed.points[0].depth).toBe(1000.0);
    expect(parsed.points[0].gr).toBe(45.2);
    expect(parsed.points[0].res).toBe(12.5);
    expect(parsed.points[0].rhob).toBe(2.45);
    expect(parsed.points[0].nphi).toBe(0.18);
    expect(parsed.startDepth).toBe(1000.0);
    expect(parsed.stopDepth).toBe(1000.5);
  });

  it('handles null / missing values gracefully with default fallbacks', () => {
    const lasWithNull = sampleLAS.replace('45.2   12.5   2.45   0.18', '-999.25   12.5   2.45   0.18');
    const parsed = parseLASContent(lasWithNull, 'test_well_null.las');
    expect(parsed.points[0].gr).toBe(65.0); // Default safe fallback for null GR
  });
});
