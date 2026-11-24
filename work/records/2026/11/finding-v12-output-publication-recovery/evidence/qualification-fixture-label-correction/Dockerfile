FROM sha256:0ad2c553865ebb6a95c6014686f61dd97e69f0bee617af005a2ace8f83ab89e7
LABEL org.baton.qualification-fixture=scripted-provider
USER 0:0
RUN rm -f /usr/local/bin/claude
COPY --chown=0:0 claude /usr/local/bin/claude
RUN chmod 0555 /usr/local/bin/claude
USER 65532:65532
