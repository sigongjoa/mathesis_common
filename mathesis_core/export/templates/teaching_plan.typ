
// Set global font to NanumGothic for Korean support
#set text(font: "NanumGothic", size: 11pt)

// Imports
#let data_file = sys.inputs.at("data_file", default: "teaching_plan.json")
#let data = json(data_file)

// Page setup
#set page(
  paper: "a4",
  margin: (x: 2cm, y: 2.5cm),
  header: align(right)[
    #text(size: 9pt, fill: gray)[동도중학교 | #data.filename]
  ],
  footer: align(center)[
    #counter(page).display()
  ]
)

// Title
#align(center)[
  #text(size: 18pt, weight: "bold")[2025학년도 교수학습 및 평가 운영 계획]
]

#v(1cm)

// Metadata Table
#table(
  columns: (1fr, 3fr),
  stroke: 0.5pt + gray,
  inset: 8pt,
  [*학교명*], [#data.school_name],
  [*문서명*], [#data.filename],
  [*학년/학기*], [#data.year 학년도]
)

#v(1cm)

// Content Header
#text(size: 14pt, weight: "bold")[1. 교과 운영 목표]
#v(0.5cm)
본 계획은 2015 개정 교육과정에 의거하여 학생들의 창의융합적 사고력 신장과 바른 인성 함양을 목적으로 수립되었습니다.

#v(0.5cm)

// Content Table
#table(
  columns: (1fr, 4fr),
  fill: (col, row) => if row == 0 { luma(240) } else { white },
  stroke: 0.5pt + black,
  inset: 10pt,
  [*영역*], [*세부 내용*],
  ..for item in data.curriculum_content {
    ([#item.area], [#item.detail])
  }
)

#v(1cm)
#text(size: 14pt, weight: "bold")[2. 평가 계획]
#v(0.5cm)

#table(
  columns: (1fr, 1fr, 1fr, 2fr),
  fill: (col, row) => if row == 0 { luma(240) } else { white },
  stroke: 0.5pt + black,
  inset: 8pt,
  align: center,
  [*평가 시기*], [*평가 종류*], [*반영 비율*], [*평가 내용*],
  [4월 말], [지필평가], [30%], [선택형 및 서답형 혼합],
  [7월 초], [지필평가], [30%], [학기말 종합 평가],
  [상시], [수행평가], [40%], [포트폴리오, 주제 탐구 보고서]
)

#v(2cm)
#align(right)[
  *2025년 03월 02일* \
  *동도중학교장*
]
