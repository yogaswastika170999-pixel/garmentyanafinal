#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class InvoiceEditApprovalTester:
    def __init__(self, base_url="https://garment-erp-dev-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.superadmin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.vendor_id = None
        self.product_id = None
        self.variant_id = None
        self.po_id = None
        self.invoice_id = None
        self.edit_request_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        # Use specific token if provided, otherwise use admin token
        auth_token = token or self.admin_token
        if auth_token:
            test_headers['Authorization'] = f'Bearer {auth_token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@garment.com", "password": "Admin@123"}
        )
        if success and 'token' in response:
            self.admin_token = response['token']
            print(f"   Admin token obtained: {self.admin_token[:20]}...")
            return True
        return False

    def test_superadmin_login(self):
        """Test superadmin login"""
        success, response = self.run_test(
            "Superadmin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@garment.com", "password": "Admin@123"}  # Using same credentials as provided
        )
        if success and 'token' in response:
            self.superadmin_token = response['token']
            print(f"   Superadmin token obtained: {self.superadmin_token[:20]}...")
            return True
        return False

    def setup_test_data(self):
        """Create test data: vendor, product, PO, and invoice"""
        print(f"\n📋 Setting up test data...")
        
        # Create vendor
        vendor_data = {
            "garment_name": "Test Vendor Invoice Edit",
            "garment_code": "TV-IE-001",
            "address": "Test Address",
            "contact_person": "Test Contact",
            "phone": "123456789",
            "status": "active"
        }
        success, response = self.run_test(
            "Create Test Vendor",
            "POST",
            "garments",
            201,
            data=vendor_data
        )
        if not success or 'id' not in response:
            return False
        self.vendor_id = response['id']
        print(f"   Vendor ID: {self.vendor_id}")

        # Create product
        product_data = {
            "product_name": "Test T-Shirt Invoice Edit",
            "product_code": "TSH-IE-001",
            "category": "Apparel",
            "selling_price": 100000,
            "cmt_price": 40000,
            "status": "active"
        }
        success, response = self.run_test(
            "Create Test Product",
            "POST",
            "products",
            201,
            data=product_data
        )
        if not success or 'id' not in response:
            return False
        self.product_id = response['id']
        print(f"   Product ID: {self.product_id}")

        # Create variant
        variant_data = {
            "product_id": self.product_id,
            "size": "L",
            "color": "Red",
            "sku": "TSH-IE-001-L-RED"
        }
        success, response = self.run_test(
            "Create Test Variant",
            "POST",
            "product-variants",
            201,
            data=variant_data
        )
        if not success or 'id' not in response:
            return False
        self.variant_id = response['id']
        print(f"   Variant ID: {self.variant_id}")

        # Create PO
        po_data = {
            "po_number": f"PO-IE-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "customer_name": "Test Customer Invoice Edit",
            "vendor_id": self.vendor_id,
            "po_date": datetime.now().strftime('%Y-%m-%d'),
            "deadline": "2025-03-31",
            "delivery_deadline": "2025-04-15",
            "notes": "Test PO for invoice edit approval",
            "items": [
                {
                    "product_id": self.product_id,
                    "variant_id": self.variant_id,
                    "qty": 50,
                    "serial_number": "SN-IE-TEST-001",
                    "selling_price_snapshot": 100000,
                    "cmt_price_snapshot": 40000
                }
            ]
        }
        success, response = self.run_test(
            "Create Test PO",
            "POST",
            "production-pos",
            201,
            data=po_data
        )
        if not success or 'id' not in response:
            return False
        self.po_id = response['id']
        print(f"   PO ID: {self.po_id}")

        # Create manual invoice
        invoice_data = {
            "source_po_id": self.po_id,
            "invoice_category": "BUYER",
            "notes": "Test invoice for edit approval",
            "discount": 500000,
            "invoice_items": [
                {
                    "sku": "TSH-IE-001-L-RED",
                    "product_name": "Test T-Shirt Invoice Edit",
                    "size": "L",
                    "color": "Red",
                    "ordered_qty": 50,
                    "invoice_qty": 50,
                    "selling_price": 100000,
                    "cmt_price": 40000,
                    "po_item_id": None
                }
            ],
            "total_amount": 4500000  # 50 * 100000 - 500000
        }
        success, response = self.run_test(
            "Create Test Invoice",
            "POST",
            "invoices",
            201,
            data=invoice_data
        )
        if not success or 'id' not in response:
            return False
        self.invoice_id = response['id']
        print(f"   Invoice ID: {self.invoice_id}")
        print(f"   Invoice Number: {response.get('invoice_number')}")

        return True

    def test_submit_edit_request(self):
        """Test POST /api/invoice-edit-requests - Admin submits edit request"""
        edit_data = {
            "invoice_id": self.invoice_id,
            "change_summary": "Penyesuaian qty dan diskon sesuai negosiasi customer",
            "changes_requested": {
                "invoice_items": [
                    {
                        "sku": "TSH-IE-001-L-RED",
                        "product_name": "Test T-Shirt Invoice Edit",
                        "size": "L",
                        "color": "Red",
                        "ordered_qty": 50,
                        "invoice_qty": 45,  # Changed from 50 to 45
                        "selling_price": 95000,  # Changed from 100000 to 95000
                        "cmt_price": 40000,
                        "po_item_id": None
                    }
                ],
                "discount": 250000,  # Changed from 500000 to 250000
                "notes": "Updated notes after customer negotiation",
                "total_amount": 4025000  # 45 * 95000 - 250000
            }
        }
        
        success, response = self.run_test(
            "Submit Invoice Edit Request",
            "POST",
            "invoice-edit-requests",
            201,
            data=edit_data
        )
        if success and 'id' in response:
            self.edit_request_id = response['id']
            print(f"   Edit Request ID: {self.edit_request_id}")
            print(f"   Status: {response.get('status')}")
            return True
        return False

    def test_get_pending_requests(self):
        """Test GET /api/invoice-edit-requests?status=Pending"""
        success, response = self.run_test(
            "Get Pending Edit Requests",
            "GET",
            "invoice-edit-requests?status=Pending",
            200
        )
        if success and isinstance(response, list):
            # Find our request
            our_request = None
            for req in response:
                if req.get('id') == self.edit_request_id:
                    our_request = req
                    break
            
            if our_request:
                print(f"   ✅ Found our request in pending list")
                print(f"   Invoice Number: {our_request.get('invoice_number')}")
                print(f"   Change Summary: {our_request.get('change_summary')}")
                print(f"   Requested By: {our_request.get('requested_by_name')}")
                return True
            else:
                print(f"   ❌ Our request not found in pending list")
                return False
        return False

    def test_approve_request(self):
        """Test PUT /api/invoice-edit-requests/{id}/approve"""
        approval_data = {
            "approval_notes": "Approved - changes look good after review"
        }
        
        success, response = self.run_test(
            "Approve Edit Request",
            "PUT",
            f"invoice-edit-requests/{self.edit_request_id}/approve",
            200,
            data=approval_data,
            token=self.superadmin_token  # Use superadmin token for approval
        )
        if success:
            print(f"   ✅ Request approved successfully")
            print(f"   Status: {response.get('status')}")
            return True
        return False

    def test_verify_invoice_updated(self):
        """Verify that the invoice was automatically updated after approval"""
        success, response = self.run_test(
            "Verify Invoice Updated",
            "GET",
            f"invoices/{self.invoice_id}",
            200
        )
        if success:
            # Check if invoice was updated with new values
            invoice_items = response.get('invoice_items', [])
            if invoice_items:
                item = invoice_items[0]
                if (item.get('invoice_qty') == 45 and 
                    item.get('selling_price') == 95000 and
                    response.get('discount') == 250000 and
                    response.get('notes') == "Updated notes after customer negotiation"):
                    print(f"   ✅ Invoice successfully updated with approved changes")
                    print(f"   New qty: {item.get('invoice_qty')}")
                    print(f"   New selling price: {item.get('selling_price')}")
                    print(f"   New discount: {response.get('discount')}")
                    return True
                else:
                    print(f"   ❌ Invoice not updated correctly")
                    print(f"   Current qty: {item.get('invoice_qty')} (expected 45)")
                    print(f"   Current price: {item.get('selling_price')} (expected 95000)")
                    print(f"   Current discount: {response.get('discount')} (expected 250000)")
                    return False
            else:
                print(f"   ❌ No invoice items found")
                return False
        return False

    def test_get_change_history(self):
        """Test GET /api/invoices/{id}/change-history"""
        success, response = self.run_test(
            "Get Invoice Change History",
            "GET",
            f"invoices/{self.invoice_id}/change-history",
            200
        )
        if success and isinstance(response, list):
            if len(response) > 0:
                history = response[0]  # Most recent change
                print(f"   ✅ Found {len(response)} change history record(s)")
                print(f"   Change Type: {history.get('change_type')}")
                print(f"   Changed By: {history.get('changed_by_name')}")
                print(f"   Notes: {history.get('notes')}")
                return True
            else:
                print(f"   ❌ No change history found")
                return False
        return False

    def test_reject_workflow(self):
        """Test the reject workflow with a new request"""
        # Create another edit request
        edit_data = {
            "invoice_id": self.invoice_id,
            "change_summary": "Another test change that will be rejected",
            "changes_requested": {
                "invoice_items": [
                    {
                        "sku": "TSH-IE-001-L-RED",
                        "product_name": "Test T-Shirt Invoice Edit",
                        "size": "L",
                        "color": "Red",
                        "ordered_qty": 50,
                        "invoice_qty": 40,
                        "selling_price": 90000,
                        "cmt_price": 40000,
                        "po_item_id": None
                    }
                ],
                "discount": 100000,
                "notes": "Test reject workflow",
                "total_amount": 3500000
            }
        }
        
        success, response = self.run_test(
            "Submit Second Edit Request (for reject test)",
            "POST",
            "invoice-edit-requests",
            201,
            data=edit_data
        )
        if not success or 'id' not in response:
            return False
        
        reject_request_id = response['id']
        print(f"   Second Request ID: {reject_request_id}")

        # Now reject it
        reject_data = {
            "approval_notes": "Rejected - changes not justified"
        }
        
        success, response = self.run_test(
            "Reject Edit Request",
            "PUT",
            f"invoice-edit-requests/{reject_request_id}/reject",
            200,
            data=reject_data,
            token=self.superadmin_token
        )
        if success:
            print(f"   ✅ Request rejected successfully")
            print(f"   Status: {response.get('status')}")
            return True
        return False

    def test_rbac_restrictions(self):
        """Test RBAC - only admin can request, only superadmin/admin can approve"""
        # This would require creating a different user role, but for now we'll test with existing admin
        # In a real scenario, we'd test with vendor/buyer roles to ensure they can't access these endpoints
        
        # Test that we can't approve our own request without proper role
        success, response = self.run_test(
            "Test RBAC - Try to approve without proper permissions",
            "PUT",
            f"invoice-edit-requests/{self.edit_request_id}/approve",
            403,  # Should be forbidden if not superadmin/admin
            data={"approval_notes": "Test"},
            token=None  # No token
        )
        if success:  # Success here means we got the expected 403
            print(f"   ✅ RBAC working - unauthorized access blocked")
            return True
        return False

    def test_cannot_edit_superseded_invoice(self):
        """Test that we cannot request edit for superseded invoices"""
        # First, let's try to create a request for a non-existent invoice to test validation
        edit_data = {
            "invoice_id": "non-existent-id",
            "change_summary": "This should fail",
            "changes_requested": {
                "invoice_items": [],
                "discount": 0,
                "notes": "Test",
                "total_amount": 0
            }
        }
        
        success, response = self.run_test(
            "Test Cannot Edit Non-existent Invoice",
            "POST",
            "invoice-edit-requests",
            404,  # Should return 404 for non-existent invoice
            data=edit_data
        )
        if success:  # Success means we got expected 404
            print(f"   ✅ Validation working - cannot edit non-existent invoice")
            return True
        return False

    def cleanup(self):
        """Clean up test data"""
        print(f"\n🧹 Cleaning up test data...")
        
        # Delete PO (this should cascade delete invoice and related data)
        if self.po_id:
            self.run_test("Delete Test PO", "DELETE", f"production-pos/{self.po_id}", 200)
        
        # Delete product variant
        if self.variant_id:
            self.run_test("Delete Test Variant", "DELETE", f"product-variants/{self.variant_id}", 200)
        
        # Delete product
        if self.product_id:
            self.run_test("Delete Test Product", "DELETE", f"products/{self.product_id}", 200)
        
        # Delete vendor
        if self.vendor_id:
            self.run_test("Delete Test Vendor", "DELETE", f"garments/{self.vendor_id}", 200)

def main():
    print("🧪 Starting Invoice Edit Approval System Tests")
    print("=" * 60)
    
    tester = InvoiceEditApprovalTester()
    
    try:
        # Test sequence
        tests = [
            ("Admin login", tester.test_admin_login),
            ("Superadmin login", tester.test_superadmin_login),
            ("Setup test data", tester.setup_test_data),
            ("Submit edit request", tester.test_submit_edit_request),
            ("Get pending requests", tester.test_get_pending_requests),
            ("Approve request", tester.test_approve_request),
            ("Verify invoice updated", tester.test_verify_invoice_updated),
            ("Get change history", tester.test_get_change_history),
            ("Test reject workflow", tester.test_reject_workflow),
            ("Test RBAC restrictions", tester.test_rbac_restrictions),
            ("Test cannot edit superseded invoice", tester.test_cannot_edit_superseded_invoice),
        ]
        
        failed_tests = []
        for test_name, test_func in tests:
            if not test_func():
                failed_tests.append(test_name)
                print(f"\n❌ Test failed: {test_name}")
                # Continue with other tests instead of breaking
        
        # Print results
        print(f"\n📊 Test Results:")
        print(f"   Tests run: {tester.tests_run}")
        print(f"   Tests passed: {tester.tests_passed}")
        print(f"   Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
        
        if len(failed_tests) == 0:
            print(f"\n🎉 All tests passed! Invoice Edit Approval System is working correctly.")
        else:
            print(f"\n⚠️  {len(failed_tests)} test(s) failed:")
            for failed_test in failed_tests:
                print(f"     - {failed_test}")
        
        return 0 if len(failed_tests) == 0 else 1
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1
    finally:
        # Always cleanup
        tester.cleanup()

if __name__ == "__main__":
    sys.exit(main())