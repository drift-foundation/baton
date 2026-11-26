# What the packaged compose-worker must have produced for the research worker. $d is the
# sha256 of the packaged worker instructions. Used by owner-run.sh and by check.py.
.role=="research"
and .worker_id=="field-research"
and .deployment.provider_contract.adapter.context_label.roles==["research"]
and .deployment.provider_contract.adapter.research==true
and .deployment.provider_contract.adapter.provider=="claude"
and ([.deployment.provider_contract.adapter.managed_entries[].sha256]|index($d))!=null
