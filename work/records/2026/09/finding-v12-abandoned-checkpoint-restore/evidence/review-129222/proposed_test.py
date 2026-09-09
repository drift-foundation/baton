def test_nothing_outside_the_nominated_checkout_is_named(self):
    """Each command addresses the held nominated object, preserving custody."""
    sibling = os.path.join(self.temporary.name, "custody")
    os.mkdir(sibling)
    with open(os.path.join(sibling, "retained.txt"), "w") as handle:
        handle.write("immutable sibling custody\n")
    seen = []
    real = self.runner
    nominated = os.stat(self.repository)

    def recording(argv):
        self.assertEqual(tuple(argv[:2]), ("git", "-C"), argv)
        # The descriptor must still be open at the receiving boundary.
        addressed = os.stat(argv[2])
        self.assertEqual((addressed.st_dev, addressed.st_ino),
                         (nominated.st_dev, nominated.st_ino), argv)
        self.assertNotIn(sibling, argv)
        seen.append(tuple(argv))
        return real(argv)

    self.profile = GitCheckpointProfile(recording)
    self.dirty()
    self.profile.restore_checkpoint(self.repository, self.evidence)
    self.assertTrue(seen)
    for argv in seen:
        self.assertEqual(argv[:2], ("git", "-C"), argv)
        self.assertNotIn(sibling, argv)
    target = seen[0][2]
    self.assertIn(tuple(reset_vector(target, self.evidence["head"])), seen)
    self.assertIn(tuple(clean_vector(target)), seen)
    self.assertEqual(
        open(os.path.join(sibling, "retained.txt")).read(),
        "immutable sibling custody\n")
