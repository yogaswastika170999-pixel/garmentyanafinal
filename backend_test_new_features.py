#!/usr/bin/env python3

import requests
import sys
import json
import base64
from datetime import datetime, timedelta

class GarmentERPNewFeaturesTester:
    def __init__(self, base_url="https://garment-erp-dev-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.vendor_id = None
        self.product_id = None
        self.variant_id = None
        self.po_id = None
        self.vendor_shipment_id = None
        self.inspection_id = None
        self.role_id = None
        self.user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    test_headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, headers=test_headers)
                else:
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

    def test_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@garment.com", "password": "Admin@123"}
        )
        if success and 'token' in response:
            self.token = response['token']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_dashboard_analytics(self):
        """Test dashboard analytics endpoint with date filter"""
        # Test basic dashboard
        success, response = self.run_test(
            "Dashboard Basic",
            "GET",
            "dashboard",
            200
        )
        if not success:
            return False

        # Test analytics endpoint
        success, response = self.run_test(
            "Dashboard Analytics",
            "GET",
            "dashboard/analytics",
            200
        )
        if not success:
            return False

        # Test analytics with date filter
        from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        success, response = self.run_test(
            "Dashboard Analytics with Date Filter",
            "GET",
            f"dashboard/analytics?from={from_date}&to={to_date}",
            200
        )
        if success:
            print(f"   ✅ Analytics data retrieved with date filter")
            return True
        return False

    def test_serial_tracking(self):
        """Test serial tracking endpoints"""
        # Test serial list endpoint
        success, response = self.run_test(
            "Serial List",
            "GET",
            "serial-list",
            200
        )
        if not success:
            return False

        # Test with status filter
        success, response = self.run_test(
            "Serial List with Status Filter",
            "GET",
            "serial-list?status=ongoing",
            200
        )
        if not success:
            return False

        # Test with search
        success, response = self.run_test(
            "Serial List with Search",
            "GET",
            "serial-list?search=SN",
            200
        )
        if success:
            print(f"   ✅ Serial tracking endpoints working")
            return True
        return False

    def test_create_product_for_photo(self):
        """Create a test product for photo upload"""
        product_data = {
            "product_name": "Test Product for Photo",
            "product_code": "TPP-001",
            "category": "Test Category",
            "selling_price": 100000,
            "cmt_price": 50000,
            "status": "active"
        }
        success, response = self.run_test(
            "Create Product for Photo Test",
            "POST",
            "products",
            201,
            data=product_data
        )
        if success and 'id' in response:
            self.product_id = response['id']
            print(f"   Product ID: {self.product_id}")
            return True
        return False

    def test_product_photo_upload(self):
        """Test product photo upload functionality"""
        if not self.product_id:
            print("   ❌ No product ID available for photo upload test")
            return False

        # Create a simple test image (1x1 pixel PNG)
        test_image_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=='
        )
        
        files = {
            'file': ('test.png', test_image_data, 'image/png')
        }
        
        success, response = self.run_test(
            "Product Photo Upload",
            "POST",
            f"products/{self.product_id}/photo",
            200,
            files=files
        )
        if success and 'photo_url' in response:
            print(f"   ✅ Photo uploaded successfully")
            print(f"   Photo URL length: {len(response['photo_url'])}")
            return True
        return False

    def test_rbac_system(self):
        """Test RBAC (Role-Based Access Control) system"""
        # First, test getting permissions
        success, response = self.run_test(
            "Get Permissions",
            "GET",
            "permissions",
            200
        )
        if not success:
            return False

        # Create a custom role
        role_data = {
            "name": f"Test Role {datetime.now().strftime('%H%M%S')}",
            "description": "Test role for RBAC testing",
            "permissions": ["po.create", "po.view", "shipment.create", "shipment.view"]
        }
        success, response = self.run_test(
            "Create Custom Role",
            "POST",
            "roles",
            201,
            data=role_data
        )
        if success and 'id' in response:
            self.role_id = response['id']
            print(f"   Role ID: {self.role_id}")
            
            # Create a user with this role
            user_data = {
                "name": "Test User RBAC",
                "email": f"testuser{datetime.now().strftime('%H%M%S')}@test.com",
                "password": "TestPass123!",
                "role": role_data["name"],
                "status": "active"
            }
            success, response = self.run_test(
                "Create User with Custom Role",
                "POST",
                "users",
                201,
                data=user_data
            )
            if success and 'id' in response:
                self.user_id = response['id']
                print(f"   User ID: {self.user_id}")
                return True
        return False

    def test_vendor_inspection_with_accessories(self):
        """Test vendor material inspection with accessories"""
        # First create necessary test data
        if not self.create_test_data_for_inspection():
            return False

        # Create material inspection with accessories
        inspection_data = {
            "shipment_id": self.vendor_shipment_id,
            "inspection_date": datetime.now().strftime('%Y-%m-%d'),
            "overall_notes": "Test inspection with accessories",
            "items": [
                {
                    "shipment_item_id": "test-item-id",
                    "sku": "TEST-SKU",
                    "product_name": "Test Product",
                    "size": "M",
                    "color": "Blue",
                    "ordered_qty": 100,
                    "received_qty": 95,
                    "missing_qty": 5,
                    "condition_notes": "Good condition"
                }
            ],
            "accessory_items": [
                {
                    "accessory_id": "test-acc-id",
                    "accessory_name": "Test Button",
                    "accessory_code": "BTN-001",
                    "unit": "pcs",
                    "ordered_qty": 200,
                    "received_qty": 190,
                    "missing_qty": 10,
                    "condition_notes": "Some buttons damaged"
                }
            ]
        }
        
        success, response = self.run_test(
            "Create Material Inspection with Accessories",
            "POST",
            "vendor-material-inspections",
            201,
            data=inspection_data
        )
        if success and 'id' in response:
            self.inspection_id = response['id']
            print(f"   Inspection ID: {self.inspection_id}")
            
            # Verify inspection includes accessory items
            success, response = self.run_test(
                "Get Material Inspections with Accessories",
                "GET",
                "vendor-material-inspections",
                200
            )
            if success and isinstance(response, list):
                for inspection in response:
                    if inspection.get('id') == self.inspection_id:
                        if 'accessory_items' in inspection:
                            print(f"   ✅ Found accessory items in inspection")
                            return True
        return False

    def create_test_data_for_inspection(self):
        """Create minimal test data needed for inspection test"""
        # Create vendor
        vendor_data = {
            "garment_name": "Test Vendor Inspection",
            "garment_code": "TVI-001",
            "status": "active"
        }
        success, response = self.run_test(
            "Create Vendor for Inspection",
            "POST",
            "garments",
            201,
            data=vendor_data
        )
        if success and 'id' in response:
            self.vendor_id = response['id']
            
            # Create vendor shipment
            shipment_data = {
                "shipment_number": f"SHP-INSP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "vendor_id": self.vendor_id,
                "shipment_date": datetime.now().strftime('%Y-%m-%d'),
                "status": "Received",
                "items": []
            }
            success, response = self.run_test(
                "Create Vendor Shipment for Inspection",
                "POST",
                "vendor-shipments",
                201,
                data=shipment_data
            )
            if success and 'id' in response:
                self.vendor_shipment_id = response['id']
                return True
        return False

    def test_vendor_inspection_pdf_export(self):
        """Test vendor inspection PDF export functionality"""
        if not self.inspection_id:
            print("   ❌ No inspection ID available for PDF export test")
            return False

        # Test PDF export endpoint
        success, response = self.run_test(
            "Export Vendor Inspection PDF",
            "GET",
            f"vendor-material-inspections/{self.inspection_id}/export?type=vendor-inspection",
            200
        )
        if success:
            print(f"   ✅ PDF export endpoint accessible")
            return True
        return False

    def cleanup(self):
        """Clean up test data"""
        print(f"\n🧹 Cleaning up test data...")
        
        # Delete user
        if self.user_id:
            self.run_test("Delete Test User", "DELETE", f"users/{self.user_id}", 200)
        
        # Delete role
        if self.role_id:
            self.run_test("Delete Test Role", "DELETE", f"roles/{self.role_id}", 200)
        
        # Delete inspection
        if self.inspection_id:
            self.run_test("Delete Material Inspection", "DELETE", f"vendor-material-inspections/{self.inspection_id}", 200)
        
        # Delete vendor shipment
        if self.vendor_shipment_id:
            self.run_test("Delete Vendor Shipment", "DELETE", f"vendor-shipments/{self.vendor_shipment_id}", 200)
        
        # Delete product
        if self.product_id:
            self.run_test("Delete Product", "DELETE", f"products/{self.product_id}", 200)
        
        # Delete vendor
        if self.vendor_id:
            self.run_test("Delete Vendor", "DELETE", f"garments/{self.vendor_id}", 200)

def main():
    print("🧪 Starting Garment ERP New Features Tests")
    print("=" * 60)
    
    tester = GarmentERPNewFeaturesTester()
    
    try:
        # Test sequence
        tests = [
            ("Login as admin", tester.test_login),
            ("Test dashboard analytics with date filter", tester.test_dashboard_analytics),
            ("Test serial tracking endpoints", tester.test_serial_tracking),
            ("Create product for photo test", tester.test_create_product_for_photo),
            ("Test product photo upload", tester.test_product_photo_upload),
            ("Test RBAC system", tester.test_rbac_system),
            ("Test vendor inspection with accessories", tester.test_vendor_inspection_with_accessories),
            ("Test vendor inspection PDF export", tester.test_vendor_inspection_pdf_export),
        ]
        
        for test_name, test_func in tests:
            if not test_func():
                print(f"\n❌ Test failed: {test_name}")
                # Continue with other tests instead of breaking
        
        # Print results
        print(f"\n📊 Test Results:")
        print(f"   Tests run: {tester.tests_run}")
        print(f"   Tests passed: {tester.tests_passed}")
        print(f"   Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
        
        if tester.tests_passed == tester.tests_run:
            print(f"\n🎉 All tests passed! New features are working correctly.")
        else:
            print(f"\n⚠️  Some tests failed. Check the output above for details.")
        
        return 0 if tester.tests_passed == tester.tests_run else 1
        
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