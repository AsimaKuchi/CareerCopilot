import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import Navbar from "@/components/Navbar";
import AnalyzeMatchDialog from "@/components/AnalyzeMatchDialog";
import {
  Search,
  MapPin,
  Building,
  Clock,
  DollarSign,
  ExternalLink,
  Sparkles,
  FileText,
  MessageSquare,
  Loader2,
  Briefcase,
  Globe,
  Wand2,
  ArrowRight,
  FileCheck,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Target,
  Copy,
  Zap,
  GraduationCap,
  Lightbulb,
  Building,
} from "lucide-react";
import { toast } from "sonner";

const TOP_COMPANIES = [
  "Google", "Microsoft", "Amazon", "Apple", "Meta",
  "Netflix", "Tesla", "Spotify", "Uber", "Airbnb",
  "Salesforce", "Adobe", "LinkedIn",
];

export default function JobSearch({ user }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get("title") || "");
  const [location, setLocation] = useState(searchParams.get("location") || "");
  const [employmentType, setEmploymentType] = useState(searchParams.get("type") || "");
  const [companyFilter, setCompanyFilter] = useState(searchParams.get("company") || "");
  const [companyOpen, setCompanyOpen] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);
  const [showApplyDialog, setShowApplyDialog] = useState(false);
  const [applyLoading, setApplyLoading] = useState(false);
  const [generatingResume, setGeneratingResume] = useState(false);
  const [generatingCover, setGeneratingCover] = useState(false);
  const [optimizedResume, setOptimizedResume] = useState("");
  const [coverLetter, setCoverLetter] = useState("");
  const [expandedJobId, setExpandedJobId] = useState(null);
  const [jobSource, setJobSource] = useState("all");
  const [showAnalyzeDialog, setShowAnalyzeDialog] = useState(false);
  const [jobToAnalyze, setJobToAnalyze] = useState(null);
  const [showInterviewPrep, setShowInterviewPrep] = useState(false);
  const [interviewPrepJob, setInterviewPrepJob] = useState(null);
  const [interviewPrepLoading, setInterviewPrepLoading] = useState(false);
  const [interviewPrepMaterials, setInterviewPrepMaterials] = useState("");

  // Update URL params when filters change
  const updateUrlParams = (q, loc, type, company) => {
    const params = new URLSearchParams();
    if (q) params.set("title", q);
    if (loc) params.set("location", loc);
    if (type) params.set("type", type);
    if (company) params.set("company", company);
    setSearchParams(params, { replace: true });
  };

  // Track company search analytics
  const trackCompanySearch = async (company) => {
    if (!company) return;
    try {
      await fetch(`${API}/analytics/company-search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ company }),
      });
    } catch (e) { /* silent */ }
  };

  // Fetch profile and auto-search on page load
  useEffect(() => {
    fetchProfileAndSearch();
  }, []);

  const fetchProfileAndSearch = async () => {
    try {
      const response = await axios.get(`${API}/profile`, {
        withCredentials: true,
      });
      
      const profileData = response.data;
      setProfile(profileData);
      
      // Use URL params if present, otherwise auto-fill from profile
      const urlTitle = searchParams.get("title");
      const urlLocation = searchParams.get("location");
      const urlCompany = searchParams.get("company");
      
      if (urlTitle) {
        // Search from URL params (shared/bookmarked link)
        await searchJobsWithParams(urlTitle, urlLocation || "", "", "all", urlCompany || "");
      } else if (profileData.job_titles?.length > 0 || profileData.skills?.length > 0) {
        const autoQuery = profileData.job_titles?.[0] || profileData.skills?.slice(0, 3).join(" ");
        const autoLocation = profileData.preferred_locations?.[0] || "";
        
        setQuery(autoQuery);
        setLocation(autoLocation);
        
        await searchJobsWithParams(autoQuery, autoLocation, "", "all", "");
      }
    } catch (error) {
      console.error("Failed to fetch profile:", error);
    } finally {
      setInitialLoading(false);
    }
  };

  const searchJobsWithParams = async (searchQuery, searchLocation, searchEmploymentType, source = jobSource, company = companyFilter) => {
    if (!searchQuery?.trim()) {
      return;
    }

    // Update URL params
    updateUrlParams(searchQuery, searchLocation, searchEmploymentType, company);
    
    // Track company search if filter is active
    if (company) {
      trackCompanySearch(company);
    }

    setLoading(true);
    try {
      let allJobs = [];
      
      // Search quality sources (Greenhouse, Lever, Ashby)
      if (source === "greenhouse" || source === "quality" || source === "all") {
        // Search Greenhouse with streaming
        try {
          const ghResponse = await fetch(`${API}/jobs/greenhouse/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
              query: searchQuery.trim(),
              location: searchLocation?.trim() || "",
              company: company || "",
            }),
          });
          
          if (ghResponse.ok && ghResponse.body) {
            // Handle Server-Sent Events stream
            const reader = ghResponse.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let tempJobs = [];
            
            while (true) {
              const { done, value } = await reader.read();
              
              if (done) break;
              
              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n");
              buffer = lines.pop() || ""; // Keep incomplete line in buffer
              
              for (const line of lines) {
                if (line.startsWith("data: ")) {
                  const jsonStr = line.slice(6);
                  try {
                    const data = JSON.parse(jsonStr);
                    
                    if (data.heartbeat) {
                      console.log("✓ Search started, waiting for jobs...");
                    } else if (data.progress) {
                      console.log(`Progress: Checked ${data.checked} companies, found ${data.found} jobs`);
                    } else if (data.done) {
                      // Stream completed
                      console.log(`Greenhouse search completed: ${data.total} jobs found`);
                      
                      // Check if fallback is suggested (0 results for multi-word query)
                      if (data.suggest_fallback && data.total === 0) {
                        // Automatically trigger fallback search
                        console.log("No exact matches found. Searching for related roles...");
                        toast.info(`No exact "${data.original_query}" jobs found. Showing related roles in your location...`);
                        
                        // Trigger fallback search with same location, broader matching
                        setTimeout(() => {
                          performFallbackSearch(searchQuery, searchLocation, source);
                        }, 500);
                      }
                    } else {
                      // New job received - add it to temp list
                      tempJobs.push(data);
                      
                      // Update UI with new job immediately
                      const sortedJobs = [...tempJobs].sort((a, b) => {
                        const aSkip = a.match_recommendation === "skip" ? 0 : 1;
                        const bSkip = b.match_recommendation === "skip" ? 0 : 1;
                        if (aSkip !== bSkip) return bSkip - aSkip;
                        return (b.match_score || 0) - (a.match_score || 0);
                      });
                      setJobs(sortedJobs);
                    }
                  } catch (parseErr) {
                    console.error("Failed to parse SSE data:", parseErr);
                  }
                }
              }
            }
            
            // Add temp jobs to allJobs for combining with JSearch results
            allJobs = [...allJobs, ...tempJobs];
          }
        } catch (err) {
          console.error("Job search error:", err);
          toast.error("Failed to search for jobs");
        }
      }

      // Search aggregators (LinkedIn, Indeed, Glassdoor, etc.) or LinkedIn only
      if (source === "aggregator" || source === "linkedin" || source === "all") {
        try {
          const aggResponse = await fetch(`${API}/jobs/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
              query: searchQuery.trim(),
              location: searchLocation?.trim() || "",
              linkedin_only: source === "linkedin",
              company: company || "",
            }),
          });

          if (aggResponse.ok) {
            const aggData = await aggResponse.json();
            let aggJobs = aggData.jobs || [];
            
            // If linkedin source selected, filter to only LinkedIn jobs client-side as backup
            if (source === "linkedin") {
              aggJobs = aggJobs.filter(job => job.is_linkedin);
            }
            
            allJobs = [...allJobs, ...aggJobs];
          }
        } catch (err) {
          console.error("Aggregator search error:", err);
        }
      }

      // Sort and set final results
      
      // Sort combined results by match score
      allJobs.sort((a, b) => {
        const aSkip = a.match_recommendation === "skip" ? 0 : 1;
        const bSkip = b.match_recommendation === "skip" ? 0 : 1;
        if (aSkip !== bSkip) return bSkip - aSkip;
        return (b.match_score || 0) - (a.match_score || 0);
      });
      
      setJobs(allJobs);
      
      if (allJobs.length === 0) {
        if (company) {
          toast.info(`No ${searchQuery} roles at ${company} in ${searchLocation || "your area"} right now. Try removing the company filter.`);
        } else if (source === "linkedin") {
          toast.info("No LinkedIn jobs found. Try different keywords or check other sources.");
        } else {
          toast.info("No jobs found. Try different keywords.");
        }
      } else {
        const qualityCount = allJobs.filter(j => ["greenhouse", "lever", "ashby"].includes(j.source)).length;
        const linkedinCount = allJobs.filter(j => j.is_linkedin).length;
        const aggCount = allJobs.filter(j => j.source === "aggregator" && !j.is_linkedin).length;
        
        if (source === "all") {
          toast.success(`Found ${allJobs.length} jobs (${qualityCount} direct, ${linkedinCount} LinkedIn, ${aggCount} other)`);
        } else if (source === "linkedin") {
          toast.success(`Found ${allJobs.length} LinkedIn jobs`);
        } else {
          toast.success(`Found ${allJobs.length} jobs`);
        }
      }
    } catch (error) {
      toast.error("Failed to search jobs. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const performFallbackSearch = async (searchQuery, searchLocation, source) => {
    // Fallback search: Show related jobs with shared keywords, ranked by resume match
    // Keeps SAME location - never goes global
    try {
      setLoading(true);
      let allJobs = [];

      // Quality sources with fallback flag - use the STREAMING endpoint, not JSearch
      if (source === "quality" || source === "all") {
        try {
          const response = await fetch(`${API}/jobs/greenhouse/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
              query: searchQuery.trim(),
              location: searchLocation?.trim() || "",
              fallback_search: true  // Signal to backend to use broader matching
            }),
          });

          if (!response.ok) {
            throw new Error("Failed to fetch");
          }

          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";
          const tempJobs = [];

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                const jsonStr = line.slice(6);
                try {
                  const data = JSON.parse(jsonStr);

                  if (data.heartbeat || data.progress) {
                    // Ignore
                  } else if (data.done) {
                    console.log(`Fallback search completed: ${data.total} related jobs found`);
                  } else {
                    tempJobs.push(data);
                    
                    // Update UI immediately
                    const sortedJobs = [...tempJobs].sort((a, b) => {
                      return (b.match_score || 0) - (a.match_score || 0);
                    });
                    setJobs(sortedJobs);
                  }
                } catch (parseErr) {
                  console.error("Failed to parse SSE data:", parseErr);
                }
              }
            }
          }

          allJobs = [...tempJobs];
        } catch (err) {
          console.error("Fallback search error:", err);
        }
      }

      setJobs(allJobs);
      
      if (allJobs.length > 0) {
        toast.success(`Found ${allJobs.length} related roles matching your background`);
      } else {
        toast.info("No related jobs found in your location. Try broadening your search.");
      }
    } catch (error) {
      toast.error("Fallback search failed");
    } finally {
      setLoading(false);
    }
  };


  const findJobsForMe = async () => {
    if (!profile) {
      toast.error("Please complete your profile first");
      return;
    }

    if (!profile.job_titles?.length && !profile.skills?.length) {
      toast.error("Please add job titles or skills to your profile");
      return;
    }

    // Build smart query from profile
    const jobTitle = profile.job_titles?.[0] || "";
    const skills = profile.skills?.slice(0, 3).join(" ") || "";
    const smartQuery = jobTitle || skills;
    const smartLocation = profile.preferred_locations?.[0] || "";
    
    // Map job_type to employment type
    let empType = "";
    if (profile.job_type?.includes("full-time")) empType = "FULLTIME";
    else if (profile.job_type?.includes("part-time")) empType = "PARTTIME";
    else if (profile.job_type?.includes("contract")) empType = "CONTRACTOR";

    setQuery(smartQuery);
    setLocation(smartLocation);
    setEmploymentType(empType);

    await searchJobsWithParams(smartQuery, smartLocation, empType, jobSource, companyFilter);
  };

  const searchJobs = async () => {
    if (!query.trim()) {
      toast.error("Please enter a search query");
      return;
    }
    await searchJobsWithParams(query, location, employmentType, jobSource, companyFilter);
  };

  const getMatchScoreClass = (score) => {
    if (score >= 80) return "match-score-high";
    if (score >= 60) return "match-score-medium";
    return "match-score-low";
  };

  const getRecommendationBadge = (recommendation, skipReason) => {
    switch (recommendation) {
      case "strong_match":
        return { color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30", label: "Strong Match", icon: CheckCircle };
      case "good_match":
        return { color: "bg-blue-500/20 text-blue-400 border-blue-500/30", label: "Good Match", icon: CheckCircle };
      case "review":
        return { color: "bg-amber-500/20 text-amber-400 border-amber-500/30", label: "Worth Reviewing", icon: AlertCircle };
      case "not_recommended":
        return { color: "bg-red-500/20 text-red-400 border-red-500/30", label: "Not Recommended", icon: XCircle };
      case "weak_match":
        return { color: "bg-gray-500/20 text-gray-400 border-gray-500/30", label: "Weak Match", icon: AlertCircle };
      case "skip":
        return { color: "bg-red-500/20 text-red-400 border-red-500/30", label: skipReason || "Not Recommended", icon: XCircle };
      default:
        return { color: "bg-gray-500/20 text-gray-400 border-gray-500/30", label: "Unknown", icon: AlertCircle };
    }
  };

  const toggleJobExpand = (jobId) => {
    setExpandedJobId(expandedJobId === jobId ? null : jobId);
  };

  const handleApplyClick = (job) => {
    setSelectedJob(job);
    setOptimizedResume("");
    setCoverLetter("");
    setShowApplyDialog(true);
  };

  // Interview Prep Handler
  const handleInterviewPrep = async (job) => {
    setInterviewPrepJob(job);
    setInterviewPrepMaterials("");
    setShowInterviewPrep(true);
    setInterviewPrepLoading(true);

    try {
      const response = await fetch(`${API}/ai/interview-prep`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          job_title: job.job_title || job.title,
          company: job.employer_name || job.company,
          job_description: job.full_description || job.description || `${job.job_title} position at ${job.employer_name}`,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to generate prep materials");
      }

      const data = await response.json();
      setInterviewPrepMaterials(data.prep_materials);
      toast.success("Interview prep materials ready!");
    } catch (error) {
      toast.error(error.message || "Failed to generate prep materials");
      setInterviewPrepMaterials("");
    } finally {
      setInterviewPrepLoading(false);
    }
  };

  const generateOptimizedResume = async () => {
    if (!selectedJob) return;
    setGeneratingResume(true);
    try {
      const response = await axios.post(`${API}/ai/optimize-resume`, {
        job_description: selectedJob.full_description || selectedJob.description,
      }, {
        withCredentials: true,
      });

      setOptimizedResume(response.data.optimized_resume);
      toast.success("Resume optimized for ATS!");
    } catch (error) {
      const message = error.response?.data?.detail || error.message || "Failed to optimize resume";
      toast.error(message);
    } finally {
      setGeneratingResume(false);
    }
  };

  const generateCoverLetter = async () => {
    if (!selectedJob) return;
    setGeneratingCover(true);
    try {
      const response = await axios.post(`${API}/ai/cover-letter`, {
        job_title: selectedJob.title,
        company: selectedJob.company,
        job_description: selectedJob.full_description || selectedJob.description,
      }, {
        withCredentials: true,
      });

      setCoverLetter(response.data.cover_letter);
      toast.success("Cover letter generated!");
    } catch (error) {
      const message = error.response?.data?.detail || error.message || "Failed to generate cover letter";
      toast.error(message);
    } finally {
      setGeneratingCover(false);
    }
  };

  const submitApplication = async () => {
    if (!selectedJob) return;
    setApplyLoading(true);
    try {
      const response = await fetch(`${API}/applications`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          job_id: selectedJob.job_id,
          job_title: selectedJob.title,
          company: selectedJob.company,
          location: selectedJob.location,
          job_description: selectedJob.full_description || selectedJob.description,
          apply_link: selectedJob.apply_link || null,
          salary_min: selectedJob.job_min_salary || selectedJob.salary_min || null,
          salary_max: selectedJob.job_max_salary || selectedJob.salary_max || null,
          optimized_resume: optimizedResume || null,
          cover_letter: coverLetter || null,
        }),
      });

      if (!response.ok) throw new Error("Failed to save application");

      const savedDocs = [];
      if (optimizedResume) savedDocs.push("optimized resume");
      if (coverLetter) savedDocs.push("cover letter");
      
      const message = savedDocs.length > 0 
        ? `Application saved with ${savedDocs.join(" and ")}! Review it in Applications.`
        : "Application saved! Review it in Applications.";
      
      toast.success(message);
      setShowApplyDialog(false);
    } catch (error) {
      toast.error("Failed to save application");
    } finally {
      setApplyLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background" data-testid="job-search-page">
      <Navbar user={user} />
      
      <div className="hero-glow opacity-30" />

      <main className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8 animate-fade-in">
          <h1 className="text-3xl font-bold text-foreground mb-2">Find Your Perfect Job</h1>
          <p className="text-muted-foreground">
            Search thousands of jobs and get AI-powered match scores
          </p>
        </div>

        {/* Search Form */}
        <Card className="glass-light mb-8 animate-fade-in" data-testid="search-form">
          <CardContent className="p-6">
            {/* AI Find Jobs Button */}
            <div className="flex justify-center mb-6">
              <Button
                data-testid="find-jobs-for-me-btn"
                onClick={findJobsForMe}
                disabled={loading || initialLoading}
                className="bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 h-12 px-8 text-white font-medium"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                ) : (
                  <Wand2 className="w-5 h-5 mr-2" />
                )}
                Find Jobs For Me (AI-Powered)
              </Button>
            </div>

            <div className="flex items-center gap-4 mb-4">
              <div className="flex-1 h-px bg-white/10" />
              <span className="text-sm text-muted-foreground">or search manually</span>
              <div className="flex-1 h-px bg-white/10" />
            </div>

            {/* Source Selector */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-foreground">Job Sources</h2>
              <div className="inline-flex items-center gap-1 p-1 rounded-lg bg-white/5 border border-white/10">
                <button
                  onClick={() => setJobSource("all")}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    jobSource === "all" 
                      ? "bg-purple-500 text-white" 
                      : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                  }`}
                >
                  All Sources
                </button>
                <button
                  onClick={() => setJobSource("quality")}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    jobSource === "quality" 
                      ? "bg-emerald-500 text-white" 
                      : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                  }`}
                >
                  Quality Boards
                </button>
                <button
                  onClick={() => setJobSource("linkedin")}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    jobSource === "linkedin" 
                      ? "bg-blue-600 text-white" 
                      : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                  }`}
                >
                  LinkedIn
                </button>
                <button
                  onClick={() => setJobSource("aggregator")}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    jobSource === "aggregator" 
                      ? "bg-indigo-500 text-white" 
                      : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                  }`}
                >
                  Indeed & More
                </button>
              </div>
            </div>
            {jobSource === "quality" && (
              <p className="text-xs text-gray-400 mb-4">
                Searching 175+ companies on Greenhouse, Lever, Ashby, SmartRecruiters & Pinpoint
              </p>
            )}
            {jobSource === "linkedin" && (
              <p className="text-xs text-gray-400 mb-4">
                Searching LinkedIn job postings only
              </p>
            )}
            {jobSource === "aggregator" && (
              <p className="text-xs text-gray-400 mb-4">
                Searching Indeed, Glassdoor, ZipRecruiter, and other job boards
              </p>
            )}
            {jobSource === "all" && (
              <p className="text-xs text-gray-400 mb-4">
                Searching all sources for maximum results
              </p>
            )}

            {/* Search Inputs */}
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  data-testid="job-search-input"
                  placeholder="Job title, keywords, or company"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && searchJobs()}
                  className="pl-10 bg-white/5 border-white/10 h-12"
                />
              </div>
              <div className="relative md:w-48">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground z-10" />
                <Input
                  data-testid="location-input"
                  placeholder="Location"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="pl-10 bg-white/5 border-white/10 h-12"
                />
              </div>
              <Select value={employmentType} onValueChange={setEmploymentType}>
                <SelectTrigger className="md:w-40 bg-white/5 border-white/10 h-12" data-testid="employment-type-select">
                  <SelectValue placeholder="Job Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="FULLTIME">Full-time</SelectItem>
                  <SelectItem value="PARTTIME">Part-time</SelectItem>
                  <SelectItem value="CONTRACTOR">Contract</SelectItem>
                  <SelectItem value="INTERN">Internship</SelectItem>
                </SelectContent>
              </Select>
              <Popover open={companyOpen} onOpenChange={setCompanyOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={companyOpen}
                    className="md:w-48 bg-white/5 border-white/10 h-12 justify-between font-normal"
                    data-testid="company-filter-btn"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Building className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      <span className={companyFilter ? "text-foreground" : "text-muted-foreground"}>
                        {companyFilter || "Company"}
                      </span>
                    </div>
                    <ChevronDown className="ml-1 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-56 p-0" align="start">
                  <Command>
                    <CommandInput placeholder="Search company..." data-testid="company-search-input" />
                    <CommandList>
                      <CommandEmpty>No company found. Type to search.</CommandEmpty>
                      <CommandGroup>
                        <CommandItem
                          value=""
                          onSelect={() => { setCompanyFilter(""); setCompanyOpen(false); }}
                          data-testid="company-option-all"
                        >
                          All Companies
                        </CommandItem>
                      </CommandGroup>
                      <CommandSeparator />
                      <CommandGroup heading="Top Companies">
                        {TOP_COMPANIES.map((c) => (
                          <CommandItem
                            key={c}
                            value={c}
                            onSelect={(val) => { setCompanyFilter(val); setCompanyOpen(false); }}
                            data-testid={`company-option-${c.toLowerCase()}`}
                          >
                            {c}
                            {companyFilter === c && <CheckCircle className="ml-auto h-4 w-4 text-indigo-500" />}
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
              <Button
                data-testid="search-btn"
                onClick={searchJobs}
                disabled={loading}
                className="bg-indigo-500 hover:bg-indigo-600 h-12 px-8"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Search className="w-5 h-5 mr-2" />
                    Search
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Loading State */}
        {initialLoading && (
          <div className="text-center py-16">
            <Loader2 className="w-12 h-12 text-indigo-400 mx-auto mb-4 animate-spin" />
            <p className="text-muted-foreground">Finding jobs matched to your profile...</p>
          </div>
        )}

        {/* Results */}
        {!initialLoading && jobs.length > 0 && (
          <div className="space-y-4" data-testid="job-results">
            <p className="text-muted-foreground">Found {jobs.length} jobs matched to your profile</p>
            {jobs.map((job, i) => {
              const recBadge = getRecommendationBadge(job.match_recommendation, job.skip_reason);
              const RecIcon = recBadge.icon;
              const isExpanded = expandedJobId === job.job_id;
              const isNotRecommended = job.match_recommendation === "skip" || job.match_recommendation === "not_recommended";
              
              return (
              <Card
                key={job.job_id || i}
                data-testid={`job-card-${i}`}
                className={`glass-light card-hover ${isNotRecommended ? "opacity-60" : ""}`}
              >
                <CardContent className="p-6">
                  <div className="flex flex-col lg:flex-row lg:items-start gap-4">
                    {/* Company Logo */}
                    <div className="w-16 h-16 rounded-xl bg-white/5 flex items-center justify-center flex-shrink-0 overflow-hidden">
                      {job.company_logo ? (
                        <img
                          src={job.company_logo}
                          alt={job.company}
                          className="w-full h-full object-contain p-2"
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.parentElement.innerHTML = `<span class="text-2xl font-bold text-indigo-400">${job.company?.charAt(0) || 'J'}</span>`;
                          }}
                        />
                      ) : (
                        <span className="text-2xl font-bold text-indigo-400">
                          {job.company?.charAt(0) || 'J'}
                        </span>
                      )}
                    </div>

                    {/* Job Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-lg font-semibold text-foreground">{job.title}</h3>
                            {job.is_new && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 rounded text-xs font-medium">
                                ⭐ NEW
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-muted-foreground mt-1">
                            <Building className="w-4 h-4" />
                            <span>{job.company}</span>
                            {job.source === "greenhouse" && (
                              <Badge className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-1.5 py-0 text-[10px]">
                                Greenhouse
                              </Badge>
                            )}
                            {job.source === "lever" && (
                              <Badge className="bg-blue-500/20 text-blue-400 border border-blue-500/30 px-1.5 py-0 text-[10px]">
                                Lever
                              </Badge>
                            )}
                            {job.source === "ashby" && (
                              <Badge className="bg-purple-500/20 text-purple-400 border border-purple-500/30 px-1.5 py-0 text-[10px]">
                                Ashby
                              </Badge>
                            )}
                            {job.source === "smartrecruiters" && (
                              <Badge className="bg-orange-500/20 text-orange-400 border border-orange-500/30 px-1.5 py-0 text-[10px]">
                                SmartRecruiters
                              </Badge>
                            )}
                            {job.source === "pinpoint" && (
                              <Badge className="bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 px-1.5 py-0 text-[10px]">
                                Pinpoint
                              </Badge>
                            )}
                            {job.is_linkedin && (
                              <Badge className="bg-blue-600/20 text-blue-300 border border-blue-600/30 px-1.5 py-0 text-[10px]">
                                🔒 LinkedIn
                              </Badge>
                            )}
                            {job.source === "aggregator" && !job.is_linkedin && (
                              <Badge className="bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 px-1.5 py-0 text-[10px]">
                                Job Board
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <Badge className={`${getMatchScoreClass(job.match_score)} px-3 py-1`}>
                            {job.match_score}% Match
                          </Badge>
                          <Badge className={`${recBadge.color} border px-2 py-0.5 text-xs flex items-center gap-1`}>
                            <RecIcon className="w-3 h-3" />
                            {recBadge.label}
                          </Badge>
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mb-3">
                        {job.location && (
                          <div className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            <span>{job.location}</span>
                          </div>
                        )}
                        {job.employment_type && (
                          <div className="flex items-center gap-1">
                            <Briefcase className="w-4 h-4" />
                            <span className="capitalize">{job.employment_type.toLowerCase().replace('_', '-')}</span>
                          </div>
                        )}
                        {/* Show remote label with scope */}
                        {(job.remote_label || job.is_remote || job.job_is_remote) && (
                          <div className="flex items-center gap-1 text-emerald-400">
                            <Globe className="w-4 h-4" />
                            <span>{job.remote_label || "Remote"}</span>
                          </div>
                        )}
                        {/* Show hybrid indicator */}
                        {job.parsed_location?.is_hybrid && (
                          <div className="flex items-center gap-1 text-blue-400">
                            <Building className="w-4 h-4" />
                            <span>Hybrid</span>
                          </div>
                        )}
                        <div className="flex items-center gap-1">
                          <DollarSign className="w-4 h-4" />
                          <span className={(job.salary_min || job.salary_max || job.job_min_salary || job.job_max_salary) ? "text-emerald-400" : ""}>
                            {(job.salary_min || job.job_min_salary)
                              ? `$${(job.salary_min || job.job_min_salary).toLocaleString()}${(job.salary_max || job.job_max_salary) ? ` - $${(job.salary_max || job.job_max_salary).toLocaleString()}` : '+'}`
                              : "Salary not listed"}
                          </span>
                        </div>
                        {job.posted_at && (
                          <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            <span>{new Date(job.posted_at).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>

                      {/* Match Reasoning - Always visible */}
                      <p className="text-sm font-medium text-indigo-400 mb-2">
                        {job.match_reasoning}
                      </p>

                      {/* Expandable Match Details */}
                      <button 
                        onClick={() => toggleJobExpand(job.job_id)}
                        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-3 transition-colors"
                        data-testid={`expand-match-details-${i}`}
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        {isExpanded ? "Hide" : "Show"} match analysis
                      </button>

                      {isExpanded && (
                        <div className="mb-4 p-4 rounded-lg bg-white/5 border border-white/10 space-y-3">
                          {/* Grounded Strengths (new format with evidence) */}
                          {job.grounded_strengths?.length > 0 ? (
                            <div>
                              <h5 className="text-sm font-medium text-emerald-400 mb-2 flex items-center gap-1">
                                <CheckCircle className="w-4 h-4" /> Resume-Grounded Strengths
                              </h5>
                              <ul className="space-y-3">
                                {job.grounded_strengths.map((s, idx) => (
                                  <li key={idx} className="text-sm bg-emerald-500/5 p-2 rounded border-l-2 border-emerald-500/50">
                                    <div className="text-emerald-300 font-medium">{s.requirement}</div>
                                    <div className="text-muted-foreground mt-1">
                                      <span className="text-gray-400">Evidence:</span> {s.evidence}
                                    </div>
                                    <div className="text-emerald-400/80 text-xs mt-1 italic">{s.match_reason}</div>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ) : job.match_strengths?.length > 0 ? (
                            /* Fallback to old format if grounded_strengths not available */
                            <div>
                              <h5 className="text-sm font-medium text-emerald-400 mb-1 flex items-center gap-1">
                                <CheckCircle className="w-4 h-4" /> Strengths
                              </h5>
                              <ul className="space-y-1">
                                {job.match_strengths.map((s, idx) => (
                                  <li key={idx} className="text-sm text-muted-foreground pl-5">• {s}</li>
                                ))}
                              </ul>
                            </div>
                          ) : null}
                          
                          {/* Matched Skills */}
                          {job.matched_skills?.length > 0 && (
                            <div>
                              <h5 className="text-sm font-medium text-blue-400 mb-1 flex items-center gap-1">
                                <Zap className="w-4 h-4" /> Matched Skills
                              </h5>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {job.matched_skills.map((skill, idx) => (
                                  <span key={idx} className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                                    {skill}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Gaps */}
                          {job.match_gaps?.length > 0 && (
                            <div>
                              <h5 className="text-sm font-medium text-amber-400 mb-1 flex items-center gap-1">
                                <AlertCircle className="w-4 h-4" /> Potential Gaps
                              </h5>
                              <ul className="space-y-1">
                                {job.match_gaps.map((g, idx) => (
                                  <li key={idx} className="text-sm text-muted-foreground pl-5">• {g}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Skip Reason */}
                          {job.skip_reason && (
                            <div className="p-3 rounded bg-red-500/10 border border-red-500/20">
                              <p className="text-sm text-red-400 flex items-center gap-2">
                                <XCircle className="w-4 h-4 flex-shrink-0" />
                                <strong>Not recommended:</strong> {job.skip_reason}
                              </p>
                            </div>
                          )}
                        </div>
                      )}

                      <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                        {job.description}
                      </p>

                      <div className="flex flex-wrap gap-3">
                        <Button
                          onClick={() => {
                            setJobToAnalyze(job);
                            setShowAnalyzeDialog(true);
                          }}
                          className="bg-purple-500 hover:bg-purple-600"
                        >
                          <Target className="w-4 h-4 mr-2" />
                          Analyze Match
                        </Button>
                        <Button
                          onClick={() => handleInterviewPrep(job)}
                          className="bg-emerald-500 hover:bg-emerald-600"
                          data-testid={`interview-prep-btn-${i}`}
                        >
                          <GraduationCap className="w-4 h-4 mr-2" />
                          Interview Prep
                        </Button>
                        <Button
                          data-testid={`apply-btn-${i}`}
                          onClick={() => handleApplyClick(job)}
                          className="bg-indigo-500 hover:bg-indigo-600"
                          disabled={isNotRecommended}
                        >
                          <Sparkles className="w-4 h-4 mr-2" />
                          Quick Apply
                        </Button>
                        {job.apply_link && (
                          <>
                            <Button
                              variant="outline"
                              className="border-white/10"
                              onClick={(e) => {
                                e.stopPropagation();
                                console.log('Opening job link:', job.apply_link);
                                
                                if (!job.apply_link) {
                                  toast.error('Job link not available');
                                  return;
                                }
                                
                                try {
                                  const opened = window.open(job.apply_link, '_blank', 'noopener,noreferrer');
                                  if (!opened || opened.closed || typeof opened.closed === 'undefined') {
                                    // Popup was blocked
                                    toast.error('Popup blocked! Click "Copy Link" to open manually.');
                                    console.log('Popup blocked. Job URL:', job.apply_link);
                                  } else {
                                    toast.success('Opening job page in new tab...');
                                  }
                                } catch (err) {
                                  console.error('Error opening link:', err);
                                  toast.error('Failed to open. Click "Copy Link" instead.');
                                }
                              }}
                            >
                              <ExternalLink className="w-4 h-4 mr-2" />
                              View Original
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="border-white/10"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigator.clipboard.writeText(job.apply_link);
                                toast.success('Link copied! Paste in your browser to open.');
                              }}
                            >
                              <Copy className="w-3 h-3 mr-1" />
                              Copy Link
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              );
            })}
          </div>
        )}

        {/* Empty State */}
        {!loading && !initialLoading && jobs.length === 0 && (
          <div className="text-center py-16" data-testid="empty-state">
            {companyFilter ? (
              <>
                <Building className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  No {query || "matching"} roles at {companyFilter}{location ? ` in ${location}` : ""} right now.
                </h3>
                <div className="text-muted-foreground max-w-md mx-auto mb-6 space-y-1">
                  <p>Try:</p>
                  <p>- Expanding your location search</p>
                  <p>- Removing the company filter to see similar roles</p>
                  <p>- Using different job title keywords</p>
                </div>
                <div className="flex gap-3 justify-center">
                  <Button
                    variant="outline"
                    onClick={() => { setCompanyFilter(""); searchJobsWithParams(query, location, employmentType, jobSource, ""); }}
                    data-testid="clear-company-filter-btn"
                  >
                    Clear Company Filter
                  </Button>
                  <Button
                    onClick={findJobsForMe}
                    disabled={loading}
                    className="bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600"
                  >
                    <Wand2 className="w-4 h-4 mr-2" />
                    Find Jobs For Me
                  </Button>
                </div>
              </>
            ) : (
              <>
                <Wand2 className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-foreground mb-2">Ready to Find Your Dream Job?</h3>
                <p className="text-muted-foreground max-w-md mx-auto mb-6">
                  Click &quot;Find Jobs For Me&quot; to automatically discover opportunities matched to your profile, 
                  or search manually using the fields above.
                </p>
                <Button
                  onClick={findJobsForMe}
                  disabled={loading}
                  className="bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600"
                >
                  <Wand2 className="w-4 h-4 mr-2" />
                  Find Jobs For Me
                </Button>
              </>
            )}
          </div>
        )}
      </main>

      {/* Apply Dialog */}
      <Dialog open={showApplyDialog} onOpenChange={setShowApplyDialog}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden bg-background border-gray-200">
          <DialogHeader>
            <DialogTitle className="text-xl">
              Apply to {selectedJob?.title}
            </DialogTitle>
            <DialogDescription>
              {selectedJob?.company} • {selectedJob?.location}
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="max-h-[65vh] pr-4">
            <div className="space-y-6 py-4">
              {/* Resume Comparison Section */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-foreground flex items-center gap-2 text-lg">
                    <FileText className="w-5 h-5 text-emerald-500" />
                    Resume Comparison
                  </h4>
                  <Button
                    data-testid="generate-resume-btn"
                    size="sm"
                    onClick={generateOptimizedResume}
                    disabled={generatingResume || !profile?.resume_text}
                    className="bg-emerald-500 hover:bg-emerald-600"
                  >
                    {generatingResume ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                        Optimizing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Generate Optimized Version
                      </>
                    )}
                  </Button>
                </div>

                {!profile?.resume_text ? (
                  <div className="p-6 rounded-lg bg-amber-50 border border-amber-200 text-center">
                    <FileText className="w-10 h-10 text-amber-500 mx-auto mb-3" />
                    <p className="text-amber-800 font-medium">No resume uploaded yet</p>
                    <p className="text-amber-600 text-sm mt-1">Please upload your resume in your Profile to use this feature.</p>
                  </div>
                ) : (
                  <div className="grid md:grid-cols-2 gap-4 relative">
                    {/* Original Resume */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-t-lg border border-gray-200 border-b-0">
                        <FileText className="w-4 h-4 text-gray-500" />
                        <span className="font-medium text-gray-700 text-sm">Original Resume</span>
                        {profile?.resume_format && (
                          <span className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded uppercase">
                            {profile.resume_format}
                          </span>
                        )}
                        {profile?.resume_filename && (
                          <span className="ml-auto text-xs text-gray-500">{profile.resume_filename}</span>
                        )}
                      </div>
                      <div className="p-4 rounded-b-lg bg-gray-50 border border-gray-200 h-[300px] overflow-auto">
                        {/* Check if resume_text looks like base64 binary data */}
                        {profile?.resume_text && profile.resume_text.startsWith('UEsDB') ? (
                          <div className="h-full flex flex-col items-center justify-center text-center">
                            <FileText className="w-10 h-10 text-amber-400 mb-3" />
                            <p className="text-amber-700 font-medium mb-2">Resume needs re-processing</p>
                            <p className="text-gray-500 text-sm mb-4">The resume file was stored but text wasn&apos;t extracted properly.</p>
                            <Button
                              size="sm"
                              onClick={async () => {
                                try {
                                  await axios.post(`${API}/profile/resume/reparse`, {}, { withCredentials: true });
                                  toast.success("Resume text extracted! Refreshing...");
                                  window.location.reload();
                                } catch (err) {
                                  toast.error("Failed to re-extract text. Please re-upload your resume.");
                                }
                              }}
                              className="bg-amber-500 hover:bg-amber-600"
                            >
                              Re-extract Text
                            </Button>
                          </div>
                        ) : (
                          <pre className="text-sm text-gray-600 whitespace-pre-wrap font-sans leading-relaxed">
                            {profile?.resume_text || "No resume content available. Please upload your resume in your Profile."}
                          </pre>
                        )}
                      </div>
                    </div>

                    {/* Arrow indicator - centered between the two columns */}
                    <div className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 translate-y-8 z-10">
                      <div className="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center shadow-lg">
                        <ArrowRight className="w-5 h-5 text-white" />
                      </div>
                    </div>

                    {/* Optimized Resume */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 px-3 py-2 bg-emerald-100 rounded-t-lg border border-emerald-200 border-b-0">
                        <FileCheck className="w-4 h-4 text-emerald-600" />
                        <span className="font-medium text-emerald-700 text-sm">ATS-Optimized Resume</span>
                        {optimizedResume && (
                          <span className="ml-auto text-xs bg-emerald-500 text-white px-2 py-0.5 rounded-full">
                            Optimized
                          </span>
                        )}
                      </div>
                      <div className={`p-4 rounded-b-lg border h-[300px] overflow-auto ${
                        optimizedResume 
                          ? "bg-emerald-50 border-emerald-200" 
                          : "bg-gray-50 border-gray-200"
                      }`}>
                        {optimizedResume ? (
                          <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">
                            {optimizedResume}
                          </pre>
                        ) : (
                          <div className="h-full flex flex-col items-center justify-center text-center">
                            <Sparkles className="w-10 h-10 text-gray-300 mb-3" />
                            <p className="text-gray-500 text-sm">Click &quot;Generate Optimized Version&quot; to create an ATS-friendly resume tailored to this job.</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {optimizedResume && (
                  <div className="mt-4 p-4 rounded-lg bg-emerald-50 border border-emerald-200">
                    <p className="text-sm text-emerald-800">
                      <strong>What changed:</strong> Your resume has been optimized with relevant keywords from the job description 
                      while preserving your original format and structure. The same sections, layout, and formatting style have been maintained.
                    </p>
                  </div>
                )}
              </div>

              {/* Cover Letter Section */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-foreground flex items-center gap-2 text-lg">
                    <MessageSquare className="w-5 h-5 text-indigo-500" />
                    Cover Letter
                  </h4>
                  <Button
                    data-testid="generate-cover-btn"
                    size="sm"
                    onClick={generateCoverLetter}
                    disabled={generatingCover}
                    className="bg-indigo-500 hover:bg-indigo-600"
                  >
                    {generatingCover ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Generate Cover Letter
                      </>
                    )}
                  </Button>
                </div>
                {coverLetter ? (
                  <div className="p-4 rounded-lg bg-indigo-50 border border-indigo-200">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">
                      {coverLetter}
                    </pre>
                  </div>
                ) : (
                  <div className="p-6 rounded-lg bg-gray-50 border border-gray-200 text-center">
                    <MessageSquare className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500 text-sm">Click &quot;Generate Cover Letter&quot; to create a personalized cover letter for this position.</p>
                  </div>
                )}
              </div>
            </div>
          </ScrollArea>

          <DialogFooter className="border-t border-gray-200 pt-4">
            <Button
              variant="outline"
              onClick={() => setShowApplyDialog(false)}
              className="border-gray-300"
            >
              Cancel
            </Button>
            <Button
              data-testid="submit-application-btn"
              onClick={submitApplication}
              disabled={applyLoading}
              className="bg-indigo-500 hover:bg-indigo-600"
            >
              {applyLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Save Application"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Analyze Match Dialog */}
      <AnalyzeMatchDialog
        job={jobToAnalyze}
        open={showAnalyzeDialog}
        onOpenChange={setShowAnalyzeDialog}
      />

      {/* Interview Prep Dialog */}
      <Dialog open={showInterviewPrep} onOpenChange={setShowInterviewPrep}>
        <DialogContent className="max-w-4xl h-[85vh] overflow-hidden flex flex-col bg-gray-50 p-0">
          <DialogHeader className="bg-white px-6 py-4 border-b flex-shrink-0">
            <DialogTitle className="flex items-center gap-2 text-indigo-600">
              <GraduationCap className="w-5 h-5" />
              Interview Preparation
            </DialogTitle>
            <DialogDescription>
              {interviewPrepJob && (
                <span className="text-gray-600">
                  Tailored prep for <strong className="text-gray-900">{interviewPrepJob.job_title || interviewPrepJob.title}</strong> at{" "}
                  <strong className="text-gray-900">{interviewPrepJob.employer_name || interviewPrepJob.company}</strong>
                </span>
              )}
            </DialogDescription>
          </DialogHeader>

          {interviewPrepLoading ? (
            <div className="flex flex-col items-center justify-center flex-1 bg-white">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-4" />
              <p className="text-gray-600">Generating your personalized interview prep...</p>
              <p className="text-sm text-gray-400 mt-2">This may take 15-30 seconds</p>
            </div>
          ) : interviewPrepMaterials ? (
            <div className="flex-1 overflow-y-auto bg-white">
              <div className="p-6 space-y-6">
                {(() => {
                  // Parse the prep materials into sections
                  const cleanText = interviewPrepMaterials
                    .replace(/\*\*/g, '')
                    .replace(/\*/g, '')
                    .replace(/#{1,4}\s*/g, '')
                    .replace(/---/g, '')
                    .replace(/___/g, '');
                  
                  const lines = cleanText.split('\n').filter(line => line.trim());
                  const sections = [];
                  let currentSection = null;
                  let currentQA = null;
                  
                  for (const line of lines) {
                    const trimmed = line.trim();
                    
                    if (trimmed.match(/^\d+\.\s+[A-Z\s]+$/) || 
                        (trimmed === trimmed.toUpperCase() && trimmed.length > 10 && !trimmed.includes('?'))) {
                      if (currentSection) sections.push(currentSection);
                      currentSection = {
                        title: trimmed.replace(/^\d+\.\s*/, ''),
                        items: []
                      };
                      currentQA = null;
                    }
                    else if (trimmed.endsWith('?')) {
                      if (currentQA && currentSection) {
                        currentSection.items.push(currentQA);
                      }
                      currentQA = {
                        question: trimmed,
                        answer: []
                      };
                    }
                    else if (currentQA && trimmed) {
                      const cleanLine = trimmed
                        .replace(/^[-•*]\s*/, '')
                        .replace(/^>\s*/, '')
                        .replace(/^\d+\.\s*/, '');
                      if (cleanLine) {
                        currentQA.answer.push(cleanLine);
                      }
                    }
                    else if (!currentQA && currentSection && trimmed) {
                      const cleanLine = trimmed.replace(/^[-•*]\s*/, '').replace(/^>\s*/, '');
                      if (cleanLine && !cleanLine.match(/^\d+\.\s*$/)) {
                        currentSection.items.push({ tip: cleanLine });
                      }
                    }
                  }
                  
                  if (currentQA && currentSection) {
                    currentSection.items.push(currentQA);
                  }
                  if (currentSection) sections.push(currentSection);
                  
                  if (sections.length === 0) {
                    return (
                      <div className="bg-white rounded-xl p-6 border border-gray-200">
                        <p className="text-gray-900 leading-relaxed whitespace-pre-wrap">
                          {cleanText}
                        </p>
                      </div>
                    );
                  }
                  
                  return sections.map((section, sIdx) => (
                    <div key={sIdx} className="space-y-4">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
                          <span className="text-white font-bold text-sm">{sIdx + 1}</span>
                        </div>
                        <h2 className="text-xl font-bold text-indigo-600 uppercase tracking-wide">
                          {section.title}
                        </h2>
                      </div>
                      
                      <div className="space-y-4 ml-2">
                        {section.items.map((item, qIdx) => (
                          item.question ? (
                            <div 
                              key={qIdx} 
                              className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm"
                            >
                              <div className="bg-indigo-100 px-5 py-4 border-b border-indigo-200">
                                <div className="flex items-start gap-3">
                                  <span className="bg-indigo-600 text-white text-xs font-bold px-2.5 py-1.5 rounded mt-0.5 uppercase tracking-wide">
                                    Q
                                  </span>
                                  <p className="text-gray-900 font-bold text-base leading-relaxed">
                                    {item.question}
                                  </p>
                                </div>
                              </div>
                              
                              <div className="px-5 py-4 bg-emerald-50">
                                <div className="flex items-start gap-3">
                                  <span className="bg-emerald-600 text-white text-xs font-bold px-2.5 py-1.5 rounded mt-0.5 uppercase tracking-wide">
                                    A
                                  </span>
                                  <div className="space-y-2 flex-1">
                                    {item.answer.map((line, lIdx) => (
                                      <p key={lIdx} className="text-gray-700 leading-relaxed">
                                        {line}
                                      </p>
                                    ))}
                                    {item.answer.length === 0 && (
                                      <p className="text-gray-500 italic">
                                        Prepare your own answer based on your experience.
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ) : item.tip ? (
                            <div 
                              key={qIdx}
                              className="bg-amber-50 rounded-xl px-5 py-4 border border-amber-200"
                            >
                              <div className="flex items-start gap-3">
                                <Lightbulb className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                                <p className="text-gray-800 leading-relaxed">{item.tip}</p>
                              </div>
                            </div>
                          ) : null
                        ))}
                      </div>
                    </div>
                  ));
                })()}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center flex-1 text-gray-500 bg-white">
              <AlertCircle className="w-8 h-8 mb-4" />
              <p>No prep materials available. Try again.</p>
            </div>
          )}

          <div className="flex justify-end gap-2 p-4 bg-white border-t border-gray-200 flex-shrink-0">
            <Button
              variant="outline"
              onClick={() => {
                if (interviewPrepMaterials) {
                  navigator.clipboard.writeText(interviewPrepMaterials);
                  toast.success("Interview prep copied to clipboard!");
                }
              }}
              disabled={!interviewPrepMaterials}
              className="border-gray-300 text-gray-700 hover:bg-gray-100"
            >
              <Copy className="w-4 h-4 mr-2" />
              Copy All
            </Button>
            <Button
              onClick={() => handleInterviewPrep(interviewPrepJob)}
              disabled={interviewPrepLoading}
              className="bg-indigo-500 hover:bg-indigo-600 text-white"
            >
              {interviewPrepLoading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Wand2 className="w-4 h-4 mr-2" />
              )}
              Regenerate
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
