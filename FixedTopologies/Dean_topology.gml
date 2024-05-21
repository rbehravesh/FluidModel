graph [
  node [
    id 0
    label "dc_edge1"
    level "edge"
    shareCap 0
    shareCost 50
    color "cyan"
    latitude -3.74581688
  ]
  node [
    id 1
    label "dc_edge2"
    level "edge"
    shareCap 0
    shareCost 50
    color "cyan"
    latitude -3.772345
  ]
  node [
    id 2
    label "dc_tran1"
    level "trans"
    shareCap 0
    shareCost 10
    color "yellow"
    latitude -3.76538994
  ]
  node [
    id 3
    label "dc_core1"
    level "core"
    shareCap 1000
    shareCost 1
    color "pink"
    latitude -3.7615788
  ]
  edge [
    source 0
    target 2
    level "FH"
    distance 567
    shareCap 100
    shareCost 1
    latency 567
    label "FH Link"
  ]
  edge [
    source 0
    target 0
    level "InterDC"
    distance 0
    shareCap 10000000
    shareCost 0
    latency 0
    label "Intra DC Link"
  ]
  edge [
    source 1
    target 2
    level "FH"
    distance 400
    shareCap 100
    shareCost 1
    latency 400
    label "FH Link"
  ]
  edge [
    source 1
    target 3
    level "BH"
    distance 900
    shareCap 100
    shareCost 3
    latency 600
    label "BH Link"
  ]
  edge [
    source 1
    target 1
    level "InterDC"
    distance 0
    shareCap 10000000
    shareCost 0
    latency 0
    label "Intra DC Link"
  ]
  edge [
    source 2
    target 3
    level "BH"
    distance 450
    shareCap 100
    shareCost 1
    latency 450
    label "BH Link"
  ]
  edge [
    source 2
    target 2
    level "InterDC"
    distance 0
    shareCap 10000000
    shareCost 0
    latency 0
    label "Intra DC Link"
  ]
  edge [
    source 3
    target 3
    level "InterDC"
    distance 0
    shareCap 10000000
    shareCost 0
    latency 0
    label "Intra DC Link"
  ]
]
