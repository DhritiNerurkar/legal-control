import aiohttp
import json
from typing import Dict, List, Any, Optional
from app.core.config import settings
from app.models.database import SessionLocal, LegalOpinion

class ExternalSourcesClient:
    def __init__(self):
        self.lei_api_base = settings.LEI_API_BASE_URL
        self.sec_api_base = settings.SEC_EDGAR_BASE_URL

    async def get_lei_data(self, lei_number: str) -> Dict[str, Any]:
        """Get entity data from LEI database"""

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.lei_api_base}/lei-records/{lei_number}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_lei_response(data)
                    else:
                        return {"error": f"LEI lookup failed with status {response.status}"}

        except Exception as e:
            # Return synthetic data for demo purposes
            return self._get_synthetic_lei_data(lei_number)

    async def get_regulatory_data(self, entity_name: str, lei_number: str) -> Dict[str, Any]:
        """Get regulatory filing data"""

        try:
            # Try SEC EDGAR search
            regulatory_data = await self._search_sec_edgar(entity_name)

            if not regulatory_data.get("found"):
                # Try other regulatory sources
                regulatory_data.update(await self._search_other_regulators(entity_name, lei_number))

            return regulatory_data

        except Exception as e:
            return {"error": f"Regulatory data lookup failed: {str(e)}"}

    async def get_incorporation_data(self, entity_name: str, lei_number: str) -> Dict[str, Any]:
        """Get incorporation and corporate registry data"""

        # For demo, return synthetic data based on entity name patterns
        if "LLC" in entity_name or "LP" in entity_name:
            if "Delaware" in entity_name or any(name in entity_name for name in ["Goldman", "Bridgewater", "Two Sigma"]):
                return {
                    "jurisdiction": "Delaware, USA",
                    "incorporation_date": "1995-01-01",
                    "entity_type": "Limited Liability Company" if "LLC" in entity_name else "Limited Partnership",
                    "status": "Good Standing",
                    "registered_agent": "Corporation Service Company",
                    "source": "Delaware Division of Corporations"
                }

        if any(bank in entity_name for bank in ["Bank", "Chase", "JPMorgan"]):
            return {
                "jurisdiction": "National Banking Charter, USA",
                "incorporation_date": "1824-06-01",
                "entity_type": "National Bank",
                "status": "Active",
                "regulator": "OCC",
                "source": "OCC Corporate Activities Database"
            }

        if "plc" in entity_name.lower():
            return {
                "jurisdiction": "England and Wales",
                "incorporation_date": "1783-01-01",
                "entity_type": "Public Limited Company",
                "status": "Active",
                "regulator": "FCA",
                "source": "Companies House"
            }

        return {
            "jurisdiction": "Unknown",
            "entity_type": "Unknown",
            "status": "Unknown",
            "source": "Unable to locate incorporation records"
        }

    async def get_legal_opinion_coverage(self, entity_type: str, jurisdiction: str, products: List[str]) -> Dict[str, Any]:
        """Check legal opinion coverage from internal database"""

        db = SessionLocal()
        try:
            coverage_results = {}

            for product in products:
                # Query legal opinions table
                opinion = db.query(LegalOpinion).filter(
                    LegalOpinion.entity_type == entity_type,
                    LegalOpinion.jurisdiction == jurisdiction,
                    LegalOpinion.product == product
                ).first()

                if opinion:
                    coverage_results[product] = {
                        "opinion_available": opinion.opinion_available,
                        "opinion_provider": opinion.opinion_provider,
                        "opinion_date": opinion.opinion_date.isoformat() if opinion.opinion_date else None,
                        "netting_enforceability": opinion.netting_enforceability,
                        "close_out_netting": opinion.close_out_netting,
                        "summary": opinion.opinion_summary,
                        "limitations": opinion.limitations or []
                    }
                else:
                    coverage_results[product] = {
                        "opinion_available": False,
                        "reason": "No opinion found for entity type/jurisdiction/product combination"
                    }

            return coverage_results

        finally:
            db.close()

    async def _search_sec_edgar(self, entity_name: str) -> Dict[str, Any]:
        """Search SEC EDGAR database"""

        # For demo purposes, return synthetic regulatory data
        hedge_funds = ["Bridgewater", "Two Sigma", "Citadel", "Millennium"]
        asset_managers = ["Goldman", "BlackRock", "Man Group"]
        banks = ["JPMorgan", "Chase", "Bank"]

        if any(hf in entity_name for hf in hedge_funds):
            return {
                "found": True,
                "entity_type": "Hedge Fund",
                "regulatory_status": "SEC Registered Investment Adviser",
                "form_adv_date": "2023-12-31",
                "assets_under_management": "$150B",
                "regulatory_body": "SEC",
                "crd_number": "12345"
            }

        if any(am in entity_name for am in asset_managers):
            return {
                "found": True,
                "entity_type": "Asset Manager",
                "regulatory_status": "SEC Registered Investment Adviser",
                "form_adv_date": "2023-12-31",
                "assets_under_management": "$2T",
                "regulatory_body": "SEC",
                "crd_number": "67890"
            }

        if any(bank in entity_name for bank in banks):
            return {
                "found": True,
                "entity_type": "Commercial Bank",
                "regulatory_status": "National Bank",
                "charter_number": "1",
                "regulatory_body": "OCC",
                "fdic_insured": True
            }

        return {"found": False}

    async def _search_other_regulators(self, entity_name: str, lei_number: str) -> Dict[str, Any]:
        """Search other regulatory databases (FCA, etc.)"""

        if "plc" in entity_name.lower() or "Man Group" in entity_name:
            return {
                "fca_authorized": True,
                "fca_firm_reference": "122702",
                "permissions": ["Dealing in investments as principal", "Managing investments"],
                "regulatory_body": "FCA"
            }

        return {}

    def _parse_lei_response(self, data: Dict) -> Dict[str, Any]:
        """Parse LEI API response"""

        try:
            attributes = data.get("data", {}).get("attributes", {})
            entity = attributes.get("entity", {})

            return {
                "legal_name": entity.get("legalName", {}).get("name", ""),
                "lei_number": data.get("data", {}).get("id", ""),
                "status": attributes.get("registration", {}).get("registrationStatus", ""),
                "entity_category": entity.get("entityCategory", ""),
                "legal_jurisdiction": entity.get("legalJurisdiction", ""),
                "headquarters_address": entity.get("headquartersAddress", {}),
                "business_register_entity_id": entity.get("otherEntityNames", [])
            }

        except Exception as e:
            return {"error": f"Failed to parse LEI response: {str(e)}"}

    def _get_synthetic_lei_data(self, lei_number: str) -> Dict[str, Any]:
        """Return synthetic LEI data for demo purposes"""

        # Map LEI numbers to synthetic data
        synthetic_data = {
            "LMPQFR1LHAW71HGQGA77": {
                "legal_name": "Goldman Sachs Asset Management LLC",
                "lei_number": "LMPQFR1LHAW71HGQGA77",
                "status": "ISSUED",
                "entity_category": "FUND",
                "legal_jurisdiction": "US-DE",
                "headquarters_address": {
                    "country": "US",
                    "region": "NY"
                }
            },
            "5493006MHB84DD0ZWV18": {
                "legal_name": "Bridgewater Associates LP",
                "lei_number": "5493006MHB84DD0ZWV18",
                "status": "ISSUED",
                "entity_category": "FUND",
                "legal_jurisdiction": "US-DE",
                "headquarters_address": {
                    "country": "US",
                    "region": "CT"
                }
            },
            "7H6GLXDRUGQFU57RNE97": {
                "legal_name": "JPMorgan Chase Bank, National Association",
                "lei_number": "7H6GLXDRUGQFU57RNE97",
                "status": "ISSUED",
                "entity_category": "CREDIT_INSTITUTION",
                "legal_jurisdiction": "US",
                "headquarters_address": {
                    "country": "US",
                    "region": "NY"
                }
            }
        }

        return synthetic_data.get(lei_number, {
            "legal_name": "Unknown Entity",
            "lei_number": lei_number,
            "status": "NOT_FOUND",
            "error": "Synthetic data not available for this LEI"
        })