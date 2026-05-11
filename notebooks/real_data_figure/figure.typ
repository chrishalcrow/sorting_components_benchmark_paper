#set page("us-letter")
#set text(size: 9pt, font: "New Computer Modern")

#table(
  columns: (1fr, 0.087fr, 0.55fr),
  // Text fits content, SVGs split remaining space
  align: center,
  gutter: 0pt,
  stroke: none,

  box(width: 100%)[
    #table(
      columns: (1.3fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1.2fr, 1fr, 1fr),
      inset: 4pt,
      stroke: 0.5pt + gray,
      fill: (x, y) => {
        if x == 2 or x == 3 {
          green.lighten(85%)
        } else if x == 4 or x == 5 or x == 6 {
          orange.lighten(85%)
        } else if x == 7 or x == 8 {
          red.lighten(85%)
        } else if x == 0 or x == 1 {
          gray.lighten(80%)
        }
      },
      [Sorter], [Tot units], [BC good], [UR sua], [BC mua], [UR mua], [SLAy merges], [BC noise], [UR noise],
    )
  ],
  align()[],
  align()[],

  // --- Row 1 ---

  box(width: 100%)[
    *Lebedeva et. al., Chronic, NP2.0, 38 mins*
    #table(
      columns: (1.3fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1.2fr, 1fr, 1fr),
      inset: 4pt,
      stroke: 0.5pt + gray,
      fill: (x, y) => {
        if x == 2 or x == 3 {
          green.lighten(85%)
        } else if x == 4 or x == 5 or x == 6 {
          orange.lighten(85%)
        } else if x == 7 or x == 8 {
          red.lighten(85%)
        }
      },
      [KS4], [808], [246], [288], [489], [312], [5], [73], [208],
      [Lupin], [683], [216], [259], [460], [338], [2], [7], [86],
      [TCD2], [617], [119], [246], [491], [369], [13], [7], [2],
      [SC2], [270], [102], [133], [166], [137], [1], [2], [0],
    )
  ],
  align()[#image("drift_maps_and_probes/ucl_probe.png", height: 12.6%)],
  image("drift_maps_and_probes/ucl_drift.svg"),
  // --- Row 2 ---
  box(width: 100%)[
    *IBL, Acute, NP1.0, 67 mins*
    #table(
      columns: (1.3fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1.2fr, 1fr, 1fr),
      inset: 4pt,
      stroke: 0.5pt + gray,
      fill: (x, y) => {
        if x == 2 or x == 3 {
          green.lighten(85%)
        } else if x == 4 or x == 5 or x == 6 {
          orange.lighten(85%)
        } else if x == 7 or x == 8 {
          red.lighten(85%)
        }
      },
      [KS4], [1050], [210], [459], [673], [354], [24], [167], [237],
      [Lupin], [864], [209], [379], [601], [278], [6], [54], [207],
      [TDC2], [954], [124], [417], [778], [504], [33], [52], [33],
      [SC2], [458], [97], [170], [333], [271], [0], [28], [17],
    )
  ],
  align()[#image("drift_maps_and_probes/IBL_probe.png", height: 11.9%)],
  image("drift_maps_and_probes/IBL_drift.svg"),
  // --- Row 3 ---
  box(width: 100%)[
    *Duszkiewicz et. al., Chronic, CN 156H5, 211 mins*
    #table(
      columns: (1.3fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1.2fr, 1fr, 1fr),
      inset: 4pt,
      stroke: 0.5pt + gray,
      fill: (x, y) => {
        if x == 2 or x == 3 {
          green.lighten(85%)
        } else if x == 4 or x == 5 or x == 6 {
          orange.lighten(85%)
        } else if x == 7 or x == 8 {
          red.lighten(85%)
        }
      },
      [KS4], [174], [41], [71], [98], [68], [2], [35], [35],
      [Lupin], [162], [56], [96], [103], [63], [4], [3], [3],
      [TDC2], [191], [11], [60], [180], [128], [9], [0], [3],
      [SC2], [58], [4], [9], [53], [47], [0], [1], [2],
    )
  ],
  align()[#image("drift_maps_and_probes/Duszkiewicz_probe.png", height: 12.3%)],
  image("drift_maps_and_probes/Duszkiewicz_drift.svg"),
)
