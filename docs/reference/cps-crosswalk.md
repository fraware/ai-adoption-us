# CPS → RPS crosswalk, version `cps-2022-industry-rps-v1`

This file documents the production classification map used for 2025+ CPS composition builds. The code validates that civilian CPS detailed-industry recodes 1–51 are assigned exactly once. Code 52 (Armed Forces) and missing/unknown future codes are intentionally unmapped.

| RPS index | RPS industry | CPS `PRDTIND1` recodes |
|---:|---|---|
| 1 | Agriculture, Forestry, Fishing and Hunting | 1–2 |
| 2 | Mining, Quarrying, and Oil and Gas Extraction | 3 |
| 3 | Utilities | 24 |
| 4 | Construction | 4 |
| 5 | Manufacturing | 5–20 |
| 6 | Wholesale Trade | 21 |
| 7 | Retail Trade | 22 |
| 8 | Transportation and Warehousing | 23 |
| 9 | Information | 25–31 |
| 10 | Finance and Insurance | 32–33 |
| 11 | Real Estate and Rental and Leasing | 34–35 |
| 12 | Professional, Scientific, and Technical Services | 36 |
| 13 | Management of Companies and Enterprises | 37 |
| 14 | Administrative and Support and Waste Management Services | 38–39 |
| 15 | Educational Services | 40 |
| 16 | Health Care and Social Assistance | 41–43 |
| 17 | Arts, Entertainment, and Recreation | 44 |
| 18 | Accommodation and Food Services | 45–46 |
| 19 | Other Services (except Public Administration) | 47–50 |
| 20 | Public Administration | 51 |

## Occupations

CPS `PRDTOCC1` civilian values 1–22 are used one-for-one with RPS `OCC1..OCC22`:

1. Management
2. Business and Financial Operations
3. Computer and Mathematical
4. Architecture and Engineering
5. Life, Physical, and Social Science
6. Community and Social Service
7. Legal
8. Educational Instruction and Library
9. Arts, Design, Entertainment, Sports, and Media
10. Healthcare Practitioners and Technical
11. Healthcare Support
12. Protective Service
13. Food Preparation and Serving Related
14. Building and Grounds Cleaning and Maintenance
15. Personal Care and Service
16. Sales and Related
17. Office and Administrative Support
18. Farming, Fishing, and Forestry
19. Construction and Extraction
20. Installation, Maintenance, and Repair
21. Production
22. Transportation and Material Moving

CPS occupation category 23 is Armed Forces and is excluded from the civilian RPS occupation frame.

## Version boundary

This crosswalk is designed for CPS files using the 2022 Census industry classification (2025 onward). A pre-2025 historical extension must use a separate reviewed crosswalk; it must not relabel this version and reuse it silently.
