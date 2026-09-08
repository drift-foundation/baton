# Operator export

Slawomir exported the 18 named JSON files from
`/tmp/baton-w106673-k65r7btj` using the proposed sudo tar stream into this new
directory. Export observed complete on 2026-09-07; exact export UTC was not
captured. Verification by baton.prompt at 2026-09-07 03:50:26 UTC: all 18
files readable and parse as JSON; result matches the operator-supplied summary;
runner records the previously reviewed script hashes and image.

Original protected files and containers were not removed or permission-modified
by this export. These hashes bind the exported bytes; prompt did not independently
hash the protected originals. Detailed event/gate acceptance remains with reviewer.

SHA-256 (relative paths):

```text
aacbe522e457c9577626272bd6d765056e713add64619ec1720b92b3c5dedd4f  result.json
39ad94c581feef62df057376c714d8312f1c902b9a286e287e761b1313506690  runner.json
575eef8f41460ad61f40ec6488a7053b865ab179acfe79cc028361acffa46790  happy/events.json
78f0093c6357757f18f1de845e3ab688bfc01cd69544a8c2364caf6405538ef8  happy/gate.json
4cd9af403e51ca62af8c70c15f95cde9d0b04687612c72eee175e3aa58ebc512  open-file/events.json
3dc4e483ec8e7fb3942008247b8e86b09b3643764dc3f5adb30856cc1cfc2fe0  open-file/gate.json
1703dede8e369fdd916ad8c87b252d4816cefc8846046d39d0bbf6c952acc6e8  cwd/events.json
83b2e3f4cd0f955a846ba0fcdc117907d712961765832008eb0ba5bf016fcbbc  cwd/gate.json
8afb8dd29b4ff95524683c2394cb3de6f576d8e48cb81d6ce62b11ded66abd35  omitted/events.json
6f03b845e96dd5875af87ba9d0076379a41b651a187ba759e10f86ae9b165b47  omitted/gate.json
5dac104695efb0ed4da93012dede8f0569837f3952dc8183b658fb2a0fb1e9d7  before/events.json
d1cb04e03641d9bec216be7d503e73dd8265e5ec733bd58f1c365485bf94f345  before/gate.json
ac6ab3f71492fa5cfd8c8c8ded31e91b92ed116d3ba65d4a9b55bc1d7cd2f674  after/events.json
adb734eae5ef01edb1a4ce4a2edbe3810e36ce885b0b541f0ac7bb963863e8f5  after/gate.json
965fddce7351a74e6b93813f430884eb80730125e244a81e4816bd590d4d954d  stop-start-one/events.json
9bacbcf8b4b5cfa1aa52e38b69c720ad7174c8cac84fcf0091c2fdaa101d6257  stop-start-one/gate.json
d0b899cd62b068d60965f4e9a54b93a3d2cd93652f6a3b8eeeb9691596c909c2  stop-start-two/events.json
9f4644f1a23f74693308cb42111b644dd45b89a8e6715140de3f12792308621c  stop-start-two/gate.json
```
