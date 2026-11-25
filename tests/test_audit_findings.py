from qa.print_audit_findings import findings


def test_findings_identify_affected_package_version():
    report={'components':[{'bom-ref':'abc','name':'pip','version':'24.0'}],
            'vulnerabilities':[{'id':'PYSEC-test','affects':[{'ref':'abc'}]}]}
    assert list(findings(report))==[('pip','24.0','PYSEC-test')]
