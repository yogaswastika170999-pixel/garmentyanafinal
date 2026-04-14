#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class GarmentERPTester:
    def __init__(self, base_url="https://garment-erp-dev-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.vendor_id = None
        self.accessory_id = None
        self.product_id = None
        self.variant_id = None
        self.po_id = None
        self.vendor_shipment_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
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

    def test_create_vendor(self):
        """Create a test vendor"""
        vendor_data = {
            "garment_name": "Test Vendor for Accessories",
            "garment_code": "TV-ACC-001",
            "address": "Test Address",
            "contact_person": "Test Contact",
            "phone": "123456789",
            "status": "active"
        }
        success, response = self.run_test(
            "Create Vendor",
            "POST",
            "garments",
            201,
            data=vendor_data
        )
        if success and 'id' in response:
            self.vendor_id = response['id']
            print(f"   Vendor ID: {self.vendor_id}")
            return True
        return False

    def test_create_accessory(self):
        """Create a test accessory"""
        accessory_data = {
            "name": "Test Button",
            "code": "BTN-001",
            "category": "Buttons",
            "unit": "pcs",
            "description": "Test button for garments",
            "status": "active"
        }
        success, response = self.run_test(
            "Create Accessory",
            "POST",
            "accessories",
            201,
            data=accessory_data
        )
        if success and 'id' in response:
            self.accessory_id = response['id']
            print(f"   Accessory ID: {self.accessory_id}")
            return True
        return False

    def test_create_product_and_variant(self):
        """Create a test product and variant"""
        product_data = {
            "product_name": "Test T-Shirt",
            "product_code": "TSH-001",
            "category": "Apparel",
            "selling_price": 85000,
            "cmt_price": 35000,
            "status": "active"
        }
        success, response = self.run_test(
            "Create Product",
            "POST",
            "products",
            201,
            data=product_data
        )
        if success and 'id' in response:
            self.product_id = response['id']
            print(f"   Product ID: {self.product_id}")
            
            # Create variant
            variant_data = {
                "product_id": self.product_id,
                "size": "M",
                "color": "Blue",
                "sku": "TSH-001-M-BLU"
            }
            success, response = self.run_test(
                "Create Product Variant",
                "POST",
                "product-variants",
                201,
                data=variant_data
            )
            if success and 'id' in response:
                self.variant_id = response['id']
                print(f"   Variant ID: {self.variant_id}")
                return True
        return False

    def test_create_po_with_accessories(self):
        """Create a Production PO with items AND accessories"""
        po_data = {
            "po_number": f"PO-ACC-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "customer_name": "Test Customer",
            "vendor_id": self.vendor_id,
            "po_date": datetime.now().strftime('%Y-%m-%d'),
            "deadline": "2025-02-28",
            "delivery_deadline": "2025-03-15",
            "notes": "Test PO with accessories",
            "items": [
                {
                    "product_id": self.product_id,
                    "variant_id": self.variant_id,
                    "qty": 100,
                    "serial_number": "SN-TEST-001",
                    "selling_price_snapshot": 85000,
                    "cmt_price_snapshot": 35000
                }
            ]
        }
        
        success, response = self.run_test(
            "Create Production PO",
            "POST",
            "production-pos",
            201,
            data=po_data
        )
        if success and 'id' in response:
            self.po_id = response['id']
            print(f"   PO ID: {self.po_id}")
            
            # Now add accessories to the PO
            accessories_data = {
                "po_id": self.po_id,
                "items": [
                    {
                        "accessory_id": self.accessory_id,
                        "accessory_name": "Test Button",
                        "accessory_code": "BTN-001",
                        "qty_needed": 200,
                        "unit": "pcs",
                        "notes": "Buttons for test garment"
                    }
                ]
            }
            success, response = self.run_test(
                "Add Accessories to PO",
                "POST",
                "po-accessories",
                201,
                data=accessories_data
            )
            return success
        return False

    def test_get_po_detail_with_accessories(self):
        """Test GET /api/production-pos/{id} includes po_accessories"""
        success, response = self.run_test(
            "Get PO Detail with Accessories",
            "GET",
            f"production-pos/{self.po_id}",
            200
        )
        if success:
            if 'po_accessories' in response:
                accessories = response['po_accessories']
                if len(accessories) > 0:
                    print(f"   ✅ Found {len(accessories)} accessories in PO detail")
                    print(f"   Accessory: {accessories[0].get('accessory_name')} - {accessories[0].get('qty_needed')} {accessories[0].get('unit')}")
                    return True
                else:
                    print(f"   ❌ No accessories found in PO detail")
                    return False
            else:
                print(f"   ❌ po_accessories field missing from PO detail")
                return False
        return False

    def test_create_vendor_shipment(self):
        """Create a Vendor Shipment and select the PO - verify accessories from PO are displayed"""
        # First get PO items
        success, po_response = self.run_test(
            "Get PO Items",
            "GET",
            f"po-items?po_id={self.po_id}",
            200
        )
        if not success or not po_response:
            return False
            
        po_items = po_response if isinstance(po_response, list) else []
        if not po_items:
            print("   ❌ No PO items found")
            return False
            
        shipment_data = {
            "shipment_number": f"SHP-ACC-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "delivery_note_number": "DN-TEST-001",
            "vendor_id": self.vendor_id,
            "po_id": self.po_id,
            "shipment_date": datetime.now().strftime('%Y-%m-%d'),
            "notes": "Test shipment with PO accessories",
            "items": [
                {
                    "po_id": self.po_id,
                    "po_item_id": po_items[0]['id'],
                    "product_name": po_items[0]['product_name'],
                    "size": po_items[0]['size'],
                    "color": po_items[0]['color'],
                    "sku": po_items[0]['sku'],
                    "serial_number": po_items[0]['serial_number'],
                    "qty_sent": po_items[0]['qty']
                }
            ]
        }
        
        success, response = self.run_test(
            "Create Vendor Shipment",
            "POST",
            "vendor-shipments",
            201,
            data=shipment_data
        )
        if success and 'id' in response:
            self.vendor_shipment_id = response['id']
            print(f"   Vendor Shipment ID: {self.vendor_shipment_id}")
            return True
        return False

    def test_get_vendor_shipment_detail_with_accessories(self):
        """Test GET /api/vendor-shipments/{id} includes po_accessories from linked POs"""
        success, response = self.run_test(
            "Get Vendor Shipment Detail with PO Accessories",
            "GET",
            f"vendor-shipments/{self.vendor_shipment_id}",
            200
        )
        if success:
            if 'po_accessories' in response:
                accessories = response['po_accessories']
                if len(accessories) > 0:
                    print(f"   ✅ Found {len(accessories)} PO accessories in vendor shipment detail")
                    print(f"   Accessory: {accessories[0].get('accessory_name')} - {accessories[0].get('qty_needed')} {accessories[0].get('unit')}")
                    return True
                else:
                    print(f"   ❌ No PO accessories found in vendor shipment detail")
                    return False
            else:
                print(f"   ❌ po_accessories field missing from vendor shipment detail")
                return False
        return False

    def test_get_vendor_shipments_list_with_accessories_count(self):
        """Test GET /api/vendor-shipments includes po_accessories_count"""
        success, response = self.run_test(
            "Get Vendor Shipments List with Accessories Count",
            "GET",
            "vendor-shipments",
            200
        )
        if success and isinstance(response, list):
            # Find our test shipment
            test_shipment = None
            for shipment in response:
                if shipment.get('id') == self.vendor_shipment_id:
                    test_shipment = shipment
                    break
            
            if test_shipment:
                if 'po_accessories_count' in test_shipment:
                    count = test_shipment['po_accessories_count']
                    if count > 0:
                        print(f"   ✅ Found po_accessories_count: {count}")
                        return True
                    else:
                        print(f"   ❌ po_accessories_count is 0")
                        return False
                else:
                    print(f"   ❌ po_accessories_count field missing from shipment list")
                    return False
            else:
                print(f"   ❌ Test shipment not found in list")
                return False
        return False

    def test_po_accessories_api(self):
        """Test PO Accessories API endpoints"""
        # Test GET po-accessories
        success, response = self.run_test(
            "Get PO Accessories",
            "GET",
            f"po-accessories?po_id={self.po_id}",
            200
        )
        if success and isinstance(response, list) and len(response) > 0:
            print(f"   ✅ Found {len(response)} accessories via po-accessories API")
            return True
        else:
            print(f"   ❌ No accessories found via po-accessories API")
            return False

    def cleanup(self):
        """Clean up test data"""
        print(f"\n🧹 Cleaning up test data...")
        
        # Delete vendor shipment
        if self.vendor_shipment_id:
            self.run_test("Delete Vendor Shipment", "DELETE", f"vendor-shipments/{self.vendor_shipment_id}", 200)
        
        # Delete PO (this should cascade delete po_accessories)
        if self.po_id:
            self.run_test("Delete Production PO", "DELETE", f"production-pos/{self.po_id}", 200)
        
        # Delete product variant
        if self.variant_id:
            self.run_test("Delete Product Variant", "DELETE", f"product-variants/{self.variant_id}", 200)
        
        # Delete product
        if self.product_id:
            self.run_test("Delete Product", "DELETE", f"products/{self.product_id}", 200)
        
        # Delete accessory
        if self.accessory_id:
            self.run_test("Delete Accessory", "DELETE", f"accessories/{self.accessory_id}", 200)
        
        # Delete vendor
        if self.vendor_id:
            self.run_test("Delete Vendor", "DELETE", f"garments/{self.vendor_id}", 200)

def main():
    print("🧪 Starting Garment ERP Accessories Integration Tests")
    print("=" * 60)
    
    tester = GarmentERPTester()
    
    try:
        # Test sequence
        tests = [
            ("Login as admin", tester.test_login),
            ("Create vendor", tester.test_create_vendor),
            ("Create accessory", tester.test_create_accessory),
            ("Create product and variant", tester.test_create_product_and_variant),
            ("Create PO with accessories", tester.test_create_po_with_accessories),
            ("Verify PO detail includes accessories", tester.test_get_po_detail_with_accessories),
            ("Test PO Accessories API", tester.test_po_accessories_api),
            ("Create vendor shipment", tester.test_create_vendor_shipment),
            ("Verify vendor shipment detail includes PO accessories", tester.test_get_vendor_shipment_detail_with_accessories),
            ("Verify vendor shipments list includes accessories count", tester.test_get_vendor_shipments_list_with_accessories_count),
        ]
        
        for test_name, test_func in tests:
            if not test_func():
                print(f"\n❌ Test failed: {test_name}")
                break
        
        # Print results
        print(f"\n📊 Test Results:")
        print(f"   Tests run: {tester.tests_run}")
        print(f"   Tests passed: {tester.tests_passed}")
        print(f"   Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
        
        if tester.tests_passed == tester.tests_run:
            print(f"\n🎉 All tests passed! Accessories integration is working correctly.")
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