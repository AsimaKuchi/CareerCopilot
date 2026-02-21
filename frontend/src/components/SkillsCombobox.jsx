import { useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { ChevronsUpDown, Plus, Search, Check } from "lucide-react";
import { cn } from "@/lib/utils";

const SKILLS_LIST = [
  // === GENERAL / OFFICE / COMPUTER SKILLS ===
  "Microsoft Office", "Microsoft Word", "Microsoft Excel", "Excel Macros", "Excel VBA",
  "Excel Pivot Tables", "Excel VLOOKUP/XLOOKUP", "Microsoft PowerPoint", "Microsoft Outlook",
  "Microsoft Access", "Microsoft Teams", "Microsoft Visio", "Microsoft SharePoint",
  "Microsoft Project", "Google Workspace", "Google Sheets", "Google Docs", "Google Slides",
  "Gmail", "Zoom", "Slack", "Typing (60+ WPM)", "Data Entry", "Filing & Records Management",
  "Calendar Management", "Travel Coordination",
  // === OFFICE ADMINISTRATION & CLERICAL ===
  "Office Administration", "Receptionist Duties", "Scheduling & Appointments", "Phone Etiquette",
  "Meeting Coordination", "Minute Taking", "Document Formatting", "Mail Merge",
  "Office Equipment (Printers/Scanners/Fax)", "Expense Reporting", "Purchase Orders",
  "Invoice Processing", "Bookkeeping", "Payroll Processing",
  // === CUSTOMER SERVICE & RETAIL ===
  "Customer Service", "Call Center Operations", "Live Chat Support", "Complaint Resolution",
  "Retail Sales", "Point of Sale (POS) Systems", "Cash Handling", "Visual Merchandising",
  "Inventory Counting", "Loss Prevention", "Upselling", "Returns & Exchanges",
  "Customer Retention", "Zendesk", "Freshdesk", "Intercom",
  // === HEALTHCARE & MEDICAL ===
  "Patient Care", "Medical Terminology", "Electronic Health Records (EHR)", "HIPAA Compliance",
  "Vital Signs Monitoring", "Medication Administration", "Phlebotomy", "CPR/First Aid",
  "Medical Billing & Coding", "ICD-10 Coding", "Insurance Verification", "Clinical Research",
  "Lab Procedures", "Patient Scheduling", "Triage", "Epic (EHR)", "Cerner",
  // === EDUCATION & TRAINING ===
  "Teaching", "Curriculum Development", "Lesson Planning", "Classroom Management",
  "Student Assessment", "Special Education", "ESL/ELL Instruction", "Tutoring",
  "E-Learning Development", "Instructional Design", "Learning Management Systems (LMS)",
  "Training Delivery", "Workshop Facilitation", "Educational Technology",
  // === CONSTRUCTION & TRADES ===
  "Blueprint Reading", "Building Codes", "OSHA Safety", "Carpentry", "Electrical Wiring",
  "Plumbing", "HVAC Systems", "Welding", "Heavy Equipment Operation", "Concrete Work",
  "Roofing", "Painting", "Drywall Installation", "Site Supervision", "Cost Estimation",
  "AutoCAD", "SolidWorks", "Project Scheduling",
  // === MANUFACTURING & WAREHOUSE ===
  "Forklift Operation", "Warehouse Management", "Order Picking & Packing", "Shipping & Receiving",
  "Quality Control/Inspection", "Assembly Line", "CNC Machining", "Machine Operation",
  "Lean Manufacturing", "5S Methodology", "ISO 9001", "Six Sigma", "GMP (Good Manufacturing Practices)",
  "Safety Compliance", "Material Handling", "RF Scanner",
  // === FOOD SERVICE & HOSPITALITY ===
  "Food Safety (ServSafe)", "Food Preparation", "Menu Planning", "Catering",
  "Restaurant Management", "Bartending", "Barista Skills", "Hotel Front Desk",
  "Housekeeping", "Event Coordination", "Reservation Systems", "Guest Relations",
  "Banquet Operations", "Wine Knowledge",
  // === TRANSPORTATION & LOGISTICS ===
  "CDL (Commercial Driver's License)", "Route Planning", "Fleet Management",
  "Freight Management", "Customs & Import/Export", "Dispatch Operations",
  "DOT Regulations", "Last-Mile Delivery", "Load Planning",
  // === REAL ESTATE & PROPERTY ===
  "Real Estate Sales", "Property Management", "Lease Administration", "MLS Systems",
  "Real Estate Valuation", "Tenant Relations", "Building Maintenance", "Rent Collection",
  "Commercial Real Estate", "Residential Appraisal",
  // === INSURANCE ===
  "Insurance Underwriting", "Claims Processing", "Policy Administration", "Risk Assessment",
  "Actuarial Analysis", "Insurance Sales", "Reinsurance", "Workers' Compensation",
  // === BANKING & FINANCIAL SERVICES ===
  "Loan Processing", "Mortgage Origination", "Credit Analysis", "KYC/AML Compliance",
  "Wire Transfers", "Treasury Management", "Wealth Management", "Portfolio Management",
  "Financial Reporting", "Reconciliation", "Collections",
  // === LEGAL & PARALEGAL ===
  "Legal Research", "Contract Drafting", "Document Review", "Case Management",
  "E-Discovery", "Litigation Support", "Legal Writing", "Court Filing",
  "Notarization", "Immigration Law", "Corporate Law", "Family Law", "Intellectual Property Law",
  // === GOVERNMENT & PUBLIC SECTOR ===
  "Grant Writing", "Grant Management", "Policy Analysis", "Public Administration",
  "Government Procurement", "Constituent Services", "Legislative Research",
  "Emergency Management", "Urban Planning", "Environmental Compliance",
  // === NONPROFIT & SOCIAL SERVICES ===
  "Fundraising", "Donor Relations", "Program Management", "Community Outreach",
  "Case Management", "Social Work", "Crisis Intervention", "Volunteer Coordination",
  "Impact Measurement", "Advocacy",
  // === MEDIA, WRITING & COMMUNICATIONS ===
  "Content Writing", "Blog Writing", "Editing & Proofreading", "AP Style",
  "Press Releases", "Media Relations", "Public Relations", "Journalism",
  "Social Media Management", "Video Editing", "Photography", "Podcast Production",
  "Adobe Photoshop", "Adobe Illustrator", "Adobe InDesign", "Adobe Premiere Pro",
  "Adobe After Effects", "Canva", "Final Cut Pro", "DaVinci Resolve",
  // === RESEARCH & SCIENCE ===
  "Research Methodology", "Data Collection", "Survey Design", "Literature Review",
  "Peer Review", "Lab Safety", "Microscopy", "Spectroscopy",
  "Scientific Writing", "Grant Applications", "GIS/Mapping",
  // === LANGUAGES ===
  "English (Native)", "English (Fluent)", "French", "Spanish", "Mandarin Chinese",
  "Cantonese", "Hindi", "Arabic", "Portuguese", "German", "Italian", "Japanese",
  "Korean", "Russian", "Punjabi", "Tagalog", "Urdu", "American Sign Language (ASL)",
  // === PROGRAMMING LANGUAGES ===
  "JavaScript", "TypeScript", "Python", "Java", "C#", "C++", "Go", "Rust", "Ruby", "PHP",
  "Swift", "Kotlin", "Scala", "R", "MATLAB", "Perl", "Dart", "Lua", "Objective-C", "Shell/Bash",
  // === WEB & FRONTEND ===
  "React", "Angular", "Vue.js", "Next.js", "HTML/CSS", "Tailwind CSS", "Bootstrap", "Sass/SCSS",
  "Redux", "GraphQL", "REST APIs", "Node.js", "Express.js", "Django", "Flask", "Spring Boot",
  "Ruby on Rails", "ASP.NET", "Laravel", "FastAPI",
  // === MOBILE ===
  "React Native", "Flutter", "iOS Development", "Android Development", "SwiftUI", "Jetpack Compose",
  // === CLOUD & DEVOPS ===
  "AWS", "Azure", "Google Cloud (GCP)", "Docker", "Kubernetes", "Terraform", "CI/CD",
  "Jenkins", "GitHub Actions", "Linux", "Nginx", "Apache", "Serverless", "Microservices",
  // === DATA & ANALYTICS ===
  "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Apache Kafka",
  "Apache Spark", "Hadoop", "Snowflake", "BigQuery", "Redshift", "ETL Pipelines",
  "Data Warehousing", "Data Modeling", "Data Visualization",
  // === AI & MACHINE LEARNING ===
  "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "TensorFlow", "PyTorch",
  "Scikit-learn", "LLMs/GenAI", "Prompt Engineering", "MLOps",
  // === DATA SCIENCE & BI ===
  "Pandas", "NumPy", "Tableau", "Power BI", "Looker", "Excel (Advanced)",
  "Statistical Analysis", "A/B Testing", "Predictive Modeling",
  // === BUSINESS & ANALYSIS ===
  "Business Analysis", "Requirements Gathering", "Process Improvement", "SWOT Analysis",
  "Stakeholder Management", "Business Intelligence", "Market Research", "Competitive Analysis",
  "Strategic Planning", "Business Process Modeling",
  // === PROJECT & PRODUCT MANAGEMENT ===
  "Agile/Scrum", "Kanban", "JIRA", "Confluence", "Product Management", "Product Strategy",
  "Roadmap Planning", "User Stories", "Sprint Planning", "Risk Management",
  "Program Management", "Waterfall", "PMP", "PRINCE2",
  // === DESIGN & UX ===
  "Figma", "Sketch", "Adobe XD", "UI/UX Design", "User Research", "Wireframing",
  "Prototyping", "Design Systems", "Accessibility (WCAG)", "Information Architecture",
  // === MARKETING & GROWTH ===
  "Digital Marketing", "SEO/SEM", "Content Marketing", "Social Media Marketing",
  "Google Analytics", "Google Ads", "Facebook Ads", "Email Marketing", "Marketing Automation",
  "HubSpot", "Salesforce", "CRM", "Lead Generation", "Growth Hacking", "Copywriting",
  // === FINANCE & ACCOUNTING ===
  "Financial Modeling", "Financial Analysis", "FP&A", "Budgeting & Forecasting",
  "Accounting (GAAP/IFRS)", "QuickBooks", "SAP", "ERP Systems", "Auditing",
  "Tax Preparation", "Accounts Payable/Receivable", "Bloomberg Terminal",
  // === HR & PEOPLE ===
  "Talent Acquisition", "Employee Relations", "Performance Management",
  "Compensation & Benefits", "HRIS", "Workday", "ADP", "Onboarding",
  "Diversity & Inclusion", "Organizational Development",
  // === SALES & CUSTOMER SUCCESS ===
  "Sales Strategy", "Account Management", "Client Relationship Management",
  "Negotiation", "Cold Outreach", "Pipeline Management", "Customer Success",
  "Upselling/Cross-selling", "SaaS Sales", "B2B Sales", "B2C Sales",
  // === COMMUNICATION & SOFT SKILLS ===
  "Public Speaking", "Technical Writing", "Presentation Skills", "Team Leadership",
  "Cross-functional Collaboration", "Problem Solving", "Critical Thinking",
  "Communication", "Time Management", "Conflict Resolution", "Mentoring",
  "Attention to Detail", "Multitasking", "Adaptability", "Work Ethic",
  "Emotional Intelligence", "Decision Making", "Organizational Skills",
  // === OPERATIONS & SUPPLY CHAIN ===
  "Supply Chain Management", "Inventory Management", "Logistics", "Procurement",
  "Lean Six Sigma", "Quality Assurance", "Vendor Management", "Operations Management",
  // === LEGAL & COMPLIANCE ===
  "Contract Management", "Regulatory Compliance", "GDPR", "SOX Compliance",
  "Intellectual Property", "Policy Development",
  // === CYBERSECURITY ===
  "Cybersecurity", "Penetration Testing", "SOC 2", "ISO 27001", "Encryption",
  "Network Security", "Identity & Access Management", "Incident Response",
  // === OTHER TECHNICAL ===
  "Git/GitHub", "APIs", "Blockchain", "IoT", "AR/VR", "Embedded Systems",
  "Networking (TCP/IP)", "System Design", "Technical Support", "QA/Testing",
  "Selenium", "Cypress", "Performance Testing",
];

export default function SkillsCombobox({ selectedSkills = [], onAddSkill, className }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const inputRef = useRef(null);
  const wrapperRef = useRef(null);
  const dropdownRef = useRef(null);
  const [dropdownPos, setDropdownPos] = useState({ top: 0, left: 0, width: 0 });

  const existingNames = selectedSkills.map(s =>
    (typeof s === "string" ? s : s?.name || "").toLowerCase()
  );

  const filtered = SKILLS_LIST.filter(skill => {
    const skillLower = skill.toLowerCase();
    const searchLower = search.toLowerCase().trim();
    return (
      !existingNames.includes(skillLower) &&
      (searchLower === "" || skillLower.includes(searchLower))
    );
  }).slice(0, 50);

  const isCustom = search.trim() &&
    !SKILLS_LIST.some(s => s.toLowerCase() === search.trim().toLowerCase()) &&
    !existingNames.includes(search.trim().toLowerCase());

  const updatePosition = useCallback(() => {
    if (wrapperRef.current) {
      const rect = wrapperRef.current.getBoundingClientRect();
      setDropdownPos({
        top: rect.bottom + window.scrollY + 4,
        left: rect.left + window.scrollX,
        width: rect.width,
      });
    }
  }, []);

  useEffect(() => {
    if (open) updatePosition();
  }, [open, updatePosition]);

  useEffect(() => {
    if (!open) return;
    const onScroll = () => updatePosition();
    window.addEventListener("scroll", onScroll, true);
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("resize", onScroll);
    };
  }, [open, updatePosition]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        dropdownRef.current && !dropdownRef.current.contains(e.target) &&
        wrapperRef.current && !wrapperRef.current.contains(e.target)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (skillName) => {
    onAddSkill(skillName);
    setSearch("");
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && search.trim()) {
      e.preventDefault();
      if (isCustom) {
        handleSelect(search.trim());
      } else if (filtered.length > 0) {
        handleSelect(filtered[0]);
      }
    }
    if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const showDropdown = open && (filtered.length > 0 || isCustom);

  return (
    <div ref={wrapperRef} className={cn("relative", className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
        <input
          ref={inputRef}
          data-testid="skill-input"
          type="text"
          placeholder="Search skills or type a custom one..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            if (!open) setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
          className="flex h-10 w-full rounded-md border border-input bg-background pl-9 pr-10 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        />
        <button
          type="button"
          data-testid="skills-dropdown-toggle"
          onClick={() => { setOpen(!open); inputRef.current?.focus(); }}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-accent text-muted-foreground"
        >
          <ChevronsUpDown className="w-4 h-4" />
        </button>
      </div>

      {showDropdown && createPortal(
        <div
          ref={dropdownRef}
          style={{
            position: "absolute",
            top: dropdownPos.top,
            left: dropdownPos.left,
            width: dropdownPos.width,
            zIndex: 9999,
          }}
          className="max-h-64 overflow-y-auto rounded-md border bg-popover shadow-lg animate-in fade-in-0 zoom-in-95"
        >
          {isCustom && (
            <button
              data-testid="add-custom-skill-btn"
              onClick={() => handleSelect(search.trim())}
              className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-accent text-left border-b sticky top-0 bg-popover"
            >
              <Plus className="w-4 h-4 text-indigo-500 shrink-0" />
              <span>Add <strong>&quot;{search.trim()}&quot;</strong> as custom skill</span>
            </button>
          )}
          {filtered.map((skill) => (
            <button
              key={skill}
              data-testid={`skill-option-${skill.toLowerCase().replace(/[^a-z0-9]/g, "-")}`}
              onClick={() => handleSelect(skill)}
              className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-accent text-left"
            >
              <Check className="w-4 h-4 opacity-0 shrink-0" />
              <span>{skill}</span>
            </button>
          ))}
          {filtered.length === 0 && !isCustom && (
            <div className="px-3 py-6 text-sm text-muted-foreground text-center">
              No matching skills found
            </div>
          )}
        </div>,
        document.body
      )}
    </div>
  );
}
