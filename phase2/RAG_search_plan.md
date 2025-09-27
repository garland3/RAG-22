from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class QueryComplexity(Enum):
    SIMPLE = "simple"
    MULTI_HOP = "multi_hop"
    DOMAIN_UNKNOWN = "domain_unknown"
    COMPLEX_REASONING = "complex_reasoning"

class DomainConfidence(Enum):
    HIGH = "high"         # LLM understands domain well
    MEDIUM = "medium"     # Some understanding, needs supplementation
    LOW = "low"          # Little understanding, needs bootstrapping
    UNKNOWN = "unknown"   # Domain not recognized

@dataclass
class TriageResult:
    complexity: QueryComplexity
    domain_confidence: DomainConfidence
    identified_domains: List[str]
    requires_bootstrap: bool
    reasoning: str

@dataclass
class QueryPlan:
    steps: List[str]
    retrieval_strategy: str
    expected_sources: List[str]
    confidence: float

@dataclass
class DomainContext:
    domain_name: str
    key_concepts: List[str]
    terminology: Dict[str, str]
    knowledge_graph: Dict
    confidence_score: float

class MultiHopRAGSystem:
    def __init__(self):
        self.known_domains = {}  # Cache of domain contexts
        self.domain_threshold = 0.7  # Confidence threshold for domain understanding
        self.max_bootstrap_attempts = 3
        
    async def process_query(self, query: str) -> str:
        """Main entry point for query processing"""
        bootstrap_attempts = 0
        
        while bootstrap_attempts <= self.max_bootstrap_attempts:
            # STEP 1: TRIAGE
            triage_result = await self.triage_query(query)
            
            if triage_result.requires_bootstrap:
                # Domain context insufficient - bootstrap first
                print(f"🔍 Domain confidence too low ({triage_result.domain_confidence})")
                print(f"📚 Bootstrapping context for domains: {triage_result.identified_domains}")
                
                await self.bootstrap_domain_context(triage_result.identified_domains, query)
                bootstrap_attempts += 1
                
                # Re-triage after bootstrapping
                print("🔄 Re-triaging after domain bootstrap...")
                continue
            else:
                # Sufficient domain understanding - proceed with planning
                break
        
        if bootstrap_attempts > self.max_bootstrap_attempts:
            return "Unable to build sufficient domain context after multiple attempts"
        
        # STEP 2: PLANNING (now with adequate domain context)
        query_plan = await self.plan_retrieval_strategy(query, triage_result)
        
        # STEP 3: EXECUTION
        return await self.execute_multi_hop_retrieval(query, query_plan, triage_result)
    
    async def triage_query(self, query: str) -> TriageResult:
        """Analyze query to determine complexity and domain understanding"""
        
        # Extract potential domains from query
        identified_domains = await self.identify_domains(query)
        
        # Assess LLM's understanding of these domains
        domain_confidence = await self.assess_domain_confidence(identified_domains, query)
        
        # Determine query complexity
        complexity = await self.assess_complexity(query)
        
        # Decide if bootstrapping is needed
        requires_bootstrap = (
            domain_confidence in [DomainConfidence.LOW, DomainConfidence.UNKNOWN] or
            (domain_confidence == DomainConfidence.MEDIUM and complexity == QueryComplexity.COMPLEX_REASONING)
        )
        
        reasoning = f"Domains: {identified_domains}, Confidence: {domain_confidence.value}, Complexity: {complexity.value}"
        
        return TriageResult(
            complexity=complexity,
            domain_confidence=domain_confidence,
            identified_domains=identified_domains,
            requires_bootstrap=requires_bootstrap,
            reasoning=reasoning
        )
    
    async def identify_domains(self, query: str) -> List[str]:
        """Extract domain indicators from query"""
        # Use LLM to identify potential domains
        domain_prompt = f"""
        Analyze this query and identify specific domains or fields it relates to.
        Look for technical terms, industry-specific language, or specialized concepts.
        
        Query: {query}
        
        Return domains as a list. If general knowledge, return ["general"].
        """
        
        response = await self.llm_call(domain_prompt)
        # Parse response to extract domain list
        domains = self.parse_domain_list(response)
        return domains
    
    async def assess_domain_confidence(self, domains: List[str], query: str) -> DomainConfidence:
        """Assess how well the LLM understands the identified domains"""
        if "general" in domains:
            return DomainConfidence.HIGH
        
        # Check if we have cached domain context
        known_domain_count = sum(1 for domain in domains if domain in self.known_domains)
        
        if known_domain_count == len(domains):
            return DomainConfidence.HIGH
        elif known_domain_count > 0:
            return DomainConfidence.MEDIUM
        
        # Test LLM's domain knowledge with probe questions
        confidence_score = await self.probe_domain_knowledge(domains, query)
        
        if confidence_score > 0.8:
            return DomainConfidence.HIGH
        elif confidence_score > 0.5:
            return DomainConfidence.MEDIUM
        elif confidence_score > 0.2:
            return DomainConfidence.LOW
        else:
            return DomainConfidence.UNKNOWN
    
    async def probe_domain_knowledge(self, domains: List[str], original_query: str) -> float:
        """Test LLM's understanding of domain concepts"""
        probe_prompt = f"""
        For the domains {domains}, related to query "{original_query}":
        1. Define 3 key concepts for each domain
        2. Explain how these concepts might relate to the query
        3. Rate your confidence in this domain knowledge (0-10)
        
        Be honest about uncertainty.
        """
        
        response = await self.llm_call(probe_prompt)
        # Parse confidence score from response
        confidence = self.extract_confidence_score(response)
        return confidence / 10.0
    
    async def assess_complexity(self, query: str) -> QueryComplexity:
        """Determine query complexity level"""
        complexity_prompt = f"""
        Analyze query complexity. Consider:
        - Does it require multiple information sources?
        - Does it need multi-step reasoning?
        - Are there multiple sub-questions?
        - Does it require specialized domain knowledge?
        
        Query: {query}
        
        Classify as: simple, multi_hop, domain_unknown, or complex_reasoning
        """
        
        response = await self.llm_call(complexity_prompt)
        return QueryComplexity(response.strip().lower())
    
    async def bootstrap_domain_context(self, domains: List[str], original_query: str):
        """Build domain context when LLM understanding is insufficient"""
        for domain in domains:
            if domain not in self.known_domains:
                print(f"🚀 Bootstrapping context for domain: {domain}")
                
                # Strategy 1: Generate synthetic domain knowledge
                domain_context = await self.generate_domain_knowledge(domain, original_query)
                
                # Strategy 2: Query external knowledge bases
                external_context = await self.query_external_knowledge_bases(domain)
                
                # Strategy 3: Use expert-provided seed concepts (if available)
                expert_context = await self.get_expert_seed_concepts(domain)
                
                # Combine and store domain context
                combined_context = await self.combine_domain_contexts(
                    domain, domain_context, external_context, expert_context
                )
                
                self.known_domains[domain] = combined_context
                print(f"✅ Domain context built for {domain} (confidence: {combined_context.confidence_score})")
    
    async def generate_domain_knowledge(self, domain: str, context_query: str) -> DomainContext:
        """Generate synthetic domain knowledge using LLM"""
        generation_prompt = f"""
        Generate comprehensive domain knowledge for: {domain}
        Context from query: {context_query}
        
        Provide:
        1. Key concepts and terminology
        2. Common relationships between concepts
        3. Typical questions asked in this domain
        4. Important entities and their attributes
        
        Format as structured knowledge base.
        """
        
        response = await self.llm_call(generation_prompt)
        return self.parse_domain_knowledge(domain, response)
    
    async def query_external_knowledge_bases(self, domain: str) -> Dict:
        """Query external sources like DBpedia, Wikidata for domain context"""
        # Implementation would query external APIs
        # For now, return mock structure
        return {
            "entities": [],
            "relations": [],
            "concepts": [],
            "source": "external_kb"
        }
    
    async def get_expert_seed_concepts(self, domain: str) -> Dict:
        """Retrieve expert-provided seed concepts if available"""
        # Check if domain experts have provided seed concepts
        expert_seeds = {
            "medical": ["diagnosis", "treatment", "symptoms", "pathology"],
            "legal": ["precedent", "statute", "jurisdiction", "liability"],
            "biochemistry": ["enzyme", "substrate", "reaction", "pathway"]
        }
        
        return expert_seeds.get(domain, [])
    
    async def combine_domain_contexts(self, domain: str, *contexts) -> DomainContext:
        """Merge multiple domain context sources"""
        # Combine and deduplicate concepts
        all_concepts = []
        terminology = {}
        knowledge_graph = {}
        
        for context in contexts:
            if isinstance(context, DomainContext):
                all_concepts.extend(context.key_concepts)
                terminology.update(context.terminology)
                knowledge_graph.update(context.knowledge_graph)
            elif isinstance(context, dict):
                all_concepts.extend(context.get("concepts", []))
            elif isinstance(context, list):
                all_concepts.extend(context)
        
        # Remove duplicates and calculate confidence
        unique_concepts = list(set(all_concepts))
        confidence = min(1.0, len(unique_concepts) / 10.0)  # Simple confidence heuristic
        
        return DomainContext(
            domain_name=domain,
            key_concepts=unique_concepts,
            terminology=terminology,
            knowledge_graph=knowledge_graph,
            confidence_score=confidence
        )
    
    async def plan_retrieval_strategy(self, query: str, triage_result: TriageResult) -> QueryPlan:
        """Plan multi-hop retrieval strategy with domain context"""
        domain_contexts = [self.known_domains[domain] for domain in triage_result.identified_domains 
                          if domain in self.known_domains]
        
        planning_prompt = f"""
        Plan retrieval strategy for: {query}
        
        Available domain contexts: {[dc.domain_name for dc in domain_contexts]}
        Query complexity: {triage_result.complexity.value}
        
        Consider domain-specific concepts: {[dc.key_concepts for dc in domain_contexts]}
        
        Create step-by-step retrieval plan:
        1. What information to retrieve first?
        2. How to decompose into sub-queries?
        3. What retrieval methods to use?
        4. How to combine results?
        """
        
        plan_response = await self.llm_call(planning_prompt)
        return self.parse_query_plan(plan_response)
    
    async def execute_multi_hop_retrieval(self, query: str, plan: QueryPlan, triage_result: TriageResult) -> str:
        """Execute the planned multi-hop retrieval"""
        print(f"🎯 Executing {len(plan.steps)} retrieval steps")
        
        accumulated_context = []
        
        for i, step in enumerate(plan.steps):
            print(f"Step {i+1}: {step}")
            
            # Use domain-aware retrieval
            step_results = await self.domain_aware_retrieve(
                step, triage_result.identified_domains
            )
            
            accumulated_context.extend(step_results)
            
            # Evaluate if we need more information
            if await self.should_continue_retrieval(query, accumulated_context, i, plan):
                continue
            else:
                break
        
        # Generate final response using all accumulated context
        return await self.generate_final_response(query, accumulated_context, triage_result)
    
    async def domain_aware_retrieve(self, sub_query: str, domains: List[str]) -> List[str]:
        """Retrieve using domain-specific knowledge"""
        results = []
        
        for domain in domains:
            if domain in self.known_domains:
                domain_context = self.known_domains[domain]
                
                # Enhance sub-query with domain terminology
                enhanced_query = await self.enhance_with_domain_terms(sub_query, domain_context)
                
                # Retrieve using domain-specific embeddings or knowledge graph
                domain_results = await self.retrieve_from_domain(enhanced_query, domain_context)
                results.extend(domain_results)
        
        return results
    
    async def should_continue_retrieval(self, original_query: str, context: List[str], 
                                      step_index: int, plan: QueryPlan) -> bool:
        """Decide whether to continue with more retrieval steps"""
        if step_index >= len(plan.steps) - 1:
            return False
        
        # Check if we have sufficient information
        sufficiency_prompt = f"""
        Original query: {original_query}
        Retrieved so far: {context[:3]}  # Show first 3 for brevity
        
        Do we have sufficient information to answer the query? (yes/no)
        """
        
        response = await self.llm_call(sufficiency_prompt)
        return "no" in response.lower()
    
    async def generate_final_response(self, query: str, context: List[str], 
                                    triage_result: TriageResult) -> str:
        """Generate final response using accumulated context"""
        response_prompt = f"""
        Query: {query}
        Retrieved context: {context}
        Domain expertise: {triage_result.identified_domains}
        
        Generate a comprehensive, accurate response using the retrieved context.
        Cite sources and explain reasoning steps.
        """
        
        return await self.llm_call(response_prompt)
    
    # Helper methods
    async def llm_call(self, prompt: str) -> str:
        """Make LLM API call"""
        # Implementation would call actual LLM API
        return "LLM response placeholder"
    
    def parse_domain_list(self, response: str) -> List[str]:
        """Parse domain list from LLM response"""
        # Implementation to extract domain list
        return ["extracted_domain"]
    
    def extract_confidence_score(self, response: str) -> float:
        """Extract confidence score from LLM response"""
        # Implementation to parse confidence
        return 0.5
    
    def parse_domain_knowledge(self, domain: str, response: str) -> DomainContext:
        """Parse generated domain knowledge into structured format"""
        # Implementation to structure domain knowledge
        return DomainContext(domain, [], {}, {}, 0.5)
    
    def parse_query_plan(self, response: str) -> QueryPlan:
        """Parse query plan from LLM response"""
        # Implementation to extract plan steps
        return QueryPlan(["step1", "step2"], "hybrid", ["source1"], 0.8)
    
    async def enhance_with_domain_terms(self, query: str, domain_context: DomainContext) -> str:
        """Enhance query with domain-specific terminology"""
        # Add relevant domain terms to improve retrieval
        return f"{query} {' '.join(domain_context.key_concepts[:3])}"
    
    async def retrieve_from_domain(self, query: str, domain_context: DomainContext) -> List[str]:
        """Retrieve using domain-specific methods"""
        # Implementation would use domain-optimized retrieval
        return ["domain_specific_result"]

# Usage example
async def main():
    rag_system = MultiHopRAGSystem()
    
    # Example specialized domain query
    query = "What are the implications of CRISPR-Cas9 off-target effects on therapeutic applications in oncology?"
    
    response = await rag_system.process_query(query)
    print(f"Response: {response}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


    Key Design Principles:
1. Triage-First Approach
The system always starts by assessing whether it understands the domain well enough to plan effectively. If not, it bootstraps domain context before attempting any sophisticated reasoning.
2. Dynamic Domain Confidence Assessment

Probes its own knowledge with domain-specific questions
Uses multiple confidence indicators (cached domains, probe responses, complexity)
Has clear thresholds for when bootstrapping is needed

3. Multi-Strategy Bootstrapping
When domain confidence is low, it uses three parallel strategies:

Synthetic knowledge generation - LLM creates domain knowledge
External knowledge base queries - DBpedia, Wikidata, etc.
Expert seed concepts - Pre-provided domain terminology

4. Iterative Triage
After bootstrapping, it re-triages the query with the new domain context. This prevents the "planning in the dark" problem you identified.
5. Domain-Aware Execution
Once planning begins, every retrieval step is enhanced with domain-specific terminology and uses the built domain context.
Example Flow:
Query: "CRISPR-Cas9 off-target effects in oncology"

1. Triage → Identifies "biochemistry", "oncology" domains
2. Domain confidence → LOW (specialized terminology)
3. Bootstrap → Builds context for CRISPR, gene editing, cancer therapy
4. Re-triage → Now has sufficient domain understanding
5. Plan → Multi-hop strategy using domain concepts
6. Execute → Domain-enhanced retrieval and reasoning
This approach ensures the system never attempts complex planning without adequate domain understanding, directly solving the problem you raised about planning being wrong when the LLM lacks domain knowledge.RetryClaude can make mistakes. Please double-check responses.