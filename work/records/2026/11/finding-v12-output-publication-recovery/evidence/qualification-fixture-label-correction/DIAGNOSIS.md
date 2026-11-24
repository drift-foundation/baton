# Reserved runtime-label collision

The r4 supported source status diagnostic reports integrity/schema: the listed runtime includes baton.v12.qualification-fixture in the adapter-owned exact label set. This label was introduced by the qualification Dockerfile and inherited by the container. Correct fixture metadata uses org.baton.qualification-fixture. No production label validation is weakened.

Manager/publisher stopped, but the exact implementation container remained running and unrecognized. Coordinator verified its attempt ID, expected fixture image and all bind sources inside the r4 instance, then stopped only that exact container and read back exited. It remains retained; no removal was performed. Before/after inspect evidence is adjacent in ../preparation-diagnostics-correction/r4-container-*.json.

Prepared correction changes only the Dockerfile label. The scripted CLI retains sha256 ee65fa11f580a5560dfeee14781e78425f5fd58cef52c9c9c2c848b1e40d84a4 and the exact previously qualified provider base. Owner build records the image identity and asserts no reserved runtime labels. No image build performed by the coordinator.
