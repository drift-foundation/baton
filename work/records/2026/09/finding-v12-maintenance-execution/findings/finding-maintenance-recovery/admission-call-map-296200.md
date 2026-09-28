# Read-only call-site inventory, claim296200

Source sha256 da3e6cb82bfd4e2c46ef875234b88da6bd73afdd5af4462b3d6c96e0aa7c3868

Static calls, NOT observed failure counts. Read owner fixture before edits.

## CapacityCase.admit (line 479)

```python
capacity.admit_integration_execution(store, control, orchestration_id=self.ORCHESTRATION, phase=phase, execution_attempt_id=attempt_id, assignment=self.claim_of(attempt_id), input_manifest=self.configured_manifest())
```

## CapacityCase.applying (line 543)

```python
capacity.admit_integration_execution(store, self._control, orchestration_id=self.ORCHESTRATION, phase='apply', execution_attempt_id=stage['attempt_id'], assignment=self.claim_of(stage['attempt_id']), **held)
```

## ThePhasesAreSerial.test_an_admission_naming_another_participant_is_refused (line 759)

```python
capacity.admit_integration_execution(store, self.claimed('prepare-attempt-1', 'prepare-offer-1'), orchestration_id=self.ORCHESTRATION, phase='prepare', execution_attempt_id='prepare-attempt-1', assignment=dict(self.claim_of('prepare-attempt-1'), participant='baton.somebody-else'))
```

## ThePhasesAreSerial.test_a_plan_naming_an_offer_nobody_issued_is_refused (line 786)

```python
capacity.admit_integration_execution(store, control, orchestration_id=self.ORCHESTRATION, phase='prepare', execution_attempt_id='prepare-attempt-1', assignment=self.claim_of('prepare-attempt-1'), input_manifest=self.configured_manifest())
```

## ThePhasesAreSerial.test_a_plan_whose_digests_disagree_with_the_claim_is_refused (line 810)

```python
capacity.admit_integration_execution(store, control, orchestration_id=case.ORCHESTRATION, phase='prepare', execution_attempt_id='prepare-attempt-1', assignment=case.claim_of('prepare-attempt-1'))
```

## ThePhasesAreSerial.test_an_unplanned_execution_cannot_be_admitted (line 821)

```python
capacity.admit_integration_execution(store, self.claimed('prepare-attempt-1', 'prepare-offer-1'), orchestration_id=self.ORCHESTRATION, phase='prepare', execution_attempt_id='attempt-nobody-planned', assignment=self.claim_of('prepare-attempt-1'))
```

## ThePersistedEvidenceIsOwnedEndToEnd.admitting (line 1302)

```python
capacity.admit_integration_execution(store, control, orchestration_id=self.ORCHESTRATION, phase='prepare', execution_attempt_id='prepare-attempt-1', assignment=self.claim_of('prepare-attempt-1'))
```

## TheOfferIdentityIsComplete.admitting (line 1428)

```python
capacity.admit_integration_execution(store, control, orchestration_id=self.ORCHESTRATION, phase='prepare', execution_attempt_id='prepare-attempt-1', assignment=self.claim_of('prepare-attempt-1'))
```

## TheRacesUnderOneReservation.test_an_exact_repeat_replays_and_changed_operands_collide (line 1721)

```python
capacity.admit_integration_execution(store, self.control(), orchestration_id=self.ORCHESTRATION, phase='prepare', execution_attempt_id='prepare-attempt-1', assignment=self.claim_of('prepare-attempt-1'))
```

## TwoStoresContendForOneReservation.test_a_competing_admission_from_another_connection_is_refused (line 1790)

```python
capacity.admit_integration_execution(second, self._control, orchestration_id=self.ORCHESTRATION, phase='apply', execution_attempt_id=stage['attempt_id'], assignment=self.claim_of(stage['attempt_id']), coordinator=coordinator, authorization=self.authorization, grant=self.grant)
```

## TwoStoresContendForOneReservation.test_the_identical_admission_from_another_connection_replays (line 1810)

```python
capacity.admit_integration_execution(second, self._control, orchestration_id=self.ORCHESTRATION, phase='prepare', execution_attempt_id='prepare-attempt-1', assignment=self.claim_of('prepare-attempt-1'))
```

## TwoStoresContendForOneReservation.test_an_admission_that_lost_to_an_ending_is_refused (line 1828)

```python
capacity.admit_integration_execution(second, self.claimed('prepare-attempt-1', 'prepare-offer-1'), orchestration_id=self.ORCHESTRATION, phase='prepare', execution_attempt_id='prepare-attempt-1', assignment=self.claim_of('prepare-attempt-1'))
```

## TwoStoresContendForOneReservation.test_a_second_connection_waits_for_the_write_lock (line 1895)

```python
capacity.admit_integration_execution(mine, control, orchestration_id=self.ORCHESTRATION, phase='prepare', execution_attempt_id='prepare-attempt-1', assignment=assignment)
```

## TheApplyBringsItsGrantAndItsAuthorization.test_a_preparation_carrying_a_grant_is_refused (line 1980)

```python
capacity.admit_integration_execution(store, control, orchestration_id=self.ORCHESTRATION, phase='prepare', execution_attempt_id='prepare-attempt-1', assignment=self.claim_of('prepare-attempt-1'), grant=self.grant)
```

## TheStartIsBehindTheAdmission.test_a_start_after_admission_proceeds (line 2436)

```python
capacity.admit_integration_execution(store, self.control(), orchestration_id=self.ORCHESTRATION, phase='prepare', execution_attempt_id='prepare-attempt-1', assignment=self.claim_of('prepare-attempt-1'))
```

## TheStartIsBehindTheAdmission.test_the_admitted_member_is_read_from_the_store_not_remembered (line 2456)

```python
capacity.admit_integration_execution(store, self.control(), orchestration_id=self.ORCHESTRATION, phase='prepare', execution_attempt_id='prepare-attempt-1', assignment=self.claim_of('prepare-attempt-1'))
```

## TheStartIsBehindTheAdmission.test_the_parent_offer_is_not_settled_by_preparing (line 2478)

```python
capacity.admit_integration_execution(store, self.control(), orchestration_id=self.ORCHESTRATION, phase='prepare', execution_attempt_id='prepare-attempt-1', assignment=self.claim_of('prepare-attempt-1'))
```

## ThePreparationIsCoordinatedEndToEnd.prepared (line 2670)

```python
execution.prepare(orchestration_id=self.ORCHESTRATION, root_assignment_id=allocation['assignment_id'], request=self.request(), plan=self.plan(stage, **self.FRESH), execution_work_id=self.EXECUTION_WORK, execution_route=self.CHILD_ROUTE, policy_digest=self.POLICY, profile_name='reference', accept=self.accepting(), identity=self.configured_identity(), contract=self.CONTRACT)
```

## ThePreparationIsCoordinatedEndToEnd.test_a_plan_without_a_preparation_phase_refuses (line 3075)

```python
execution.prepare(orchestration_id=self.ORCHESTRATION, root_assignment_id=allocation['assignment_id'], request=self.request(), plan=[one for one in self.plan(stage, **self.FRESH) if one['phase'] != 'prepare'], execution_work_id=self.EXECUTION_WORK, execution_route='integration-preparation', policy_digest=self.POLICY, profile_name='reference', accept=self.accepting(), identity=self.IDENTITY)
```
