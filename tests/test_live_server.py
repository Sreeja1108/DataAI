import sys
from pathlib import Path
import io

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from config import Config

def test_full_wsgi_api():
    client = app.test_client()

    # 1. Index route
    r1 = client.get('/')
    assert r1.status_code == 200
    assert b"DataGuard AI" in r1.data

    # 2. Health check
    r2 = client.get('/api/health')
    assert r2.status_code == 200
    data2 = r2.get_json()
    assert data2["status"] == "online"

    # 3. Load Sample Dataset
    r3 = client.post('/api/load-sample', json={'sample_name': 'online_store_orders.csv'})
    assert r3.status_code == 200
    res3 = r3.get_json()
    assert res3["success"] is True
    data = res3['data']
    sid = data['session_id']
    assert sid is not None
    assert len(data['issues']) > 0

    # 4. Preview cleaning
    issue_id = data['issues'][0]['id']
    r4 = client.get(f'/api/preview-cleaning/{sid}/{issue_id}')
    assert r4.status_code == 200
    res4 = r4.get_json()
    assert res4["success"] is True
    assert 'preview_samples' in res4['preview']

    # 5. Apply cleaning
    r5 = client.post(f'/api/apply-cleaning/{sid}', json={'approved_issue_ids': [issue_id]})
    assert r5.status_code == 200
    res5 = r5.get_json()
    assert res5["success"] is True
    assert res5['cleaning_result']['actions_applied'] >= 1

    # 6. Generate reports
    r6 = client.post(f'/api/generate-reports/{sid}')
    assert r6.status_code == 200
    res6 = r6.get_json()
    assert res6["success"] is True
    artifacts = res6['artifacts']
    assert 'pdf_report' in artifacts
    assert 'excel_summary' in artifacts
    assert 'cleaned_csv' in artifacts

    # 7. Download PDF
    r7 = client.get(f"/api/download/{artifacts['pdf_report']}")
    assert r7.status_code == 200
    assert len(r7.data) > 1000

    # 8. File Upload via Multipart
    sample_csv_content = b"order_id,amount\nORD-1,10.5\nORD-2,20.0\n"
    r8 = client.post('/api/upload', data={
        'file': (io.BytesIO(sample_csv_content), 'test_orders.csv'),
        'user_context': 'E-commerce test batch'
    }, content_type='multipart/form-data')
    assert r8.status_code == 200
    res8 = r8.get_json()
    assert res8["success"] is True
    assert res8['data']['filename'] == 'test_orders.csv'

if __name__ == "__main__":
    test_full_wsgi_api()
    print("ALL FLASK WSGI API TESTS PASSED SUCCESSFULLY!")
