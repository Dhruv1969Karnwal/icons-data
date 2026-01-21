
package icons

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/gocolly/colly"
	"github.com/google/uuid"
)

// PendingIcon holds icon data before enrichment
type PendingIcon struct {
	Category    string
	Title       string
	Link        string
	DisplayName string
}

// IconPayload represents the enhanced structure for RAG + D2 diagram generation
type IconPayload struct {
	ID              string  `json:"id"`
	Slug            string  `json:"slug"`
	IconifyID       string  `json:"iconify_id"`
	Provider        string  `json:"provider"`
	URL             string  `json:"url"`
	SemanticProfile string  `json:"semantic_profile"`
	DisplayName     string  `json:"display_name"`
	Aliases         string  `json:"aliases"`
	Description     string  `json:"description"`
	TechnicalIntent string  `json:"technical_intent"`
	ShapeType       string  `json:"shape_type"`
	DefaultWidth    int     `json:"default_width"`
	IsContainer     bool    `json:"is_container"`
	IconPosition    string  `json:"icon_position"`
	ColorTheme      string  `json:"color_theme"`
	Popularity      float32 `json:"popularity"`
	Tags            string  `json:"tags"`
	LastScraped     string  `json:"last_scraped"`
}

// LLMEnrichmentResponse from HTTP LLM service
type LLMEnrichmentResponse struct {
	Category        string   `json:"category"`
	Aliases         []string `json:"aliases"`
	TechnicalIntent string   `json:"technical_intent"`
	SemanticProfile string   `json:"semantic_profile"`
	Tags            []string `json:"tags"`
	ShapeType       string   `json:"shape_type"`
	IsContainer     bool     `json:"is_container"`
	BrandColor      string   `json:"brand_color"`
}

// BatchClassifyRequest for parallel LLM processing
type BatchClassifyRequest struct {
	Icons []BatchIconInput `json:"icons"`
}

type BatchIconInput struct {
	Provider    string `json:"provider"`
	Title       string `json:"title"`
	DisplayName string `json:"display_name"`
}

// BatchClassifyResponse from batch endpoint
type BatchClassifyResponse struct {
	Results          []LLMEnrichmentResponse `json:"results"`
	Total            int                     `json:"total"`
	ProcessingTimeMs float64                 `json:"processing_time_ms"`
}

type IconifySearchResult struct {
	Icons []string `json:"icons"`
	Total int      `json:"total"`
}

const (
	sourceURL = "https://icons.terrastruct.com"
	outputDir = "output"
	jsonFile  = "icons_rag.json"

	useLLMEnrichment   = false
	llmServiceURL      = "http://localhost:5000/classify"
	llmBatchURL        = "http://localhost:5000/batch"
	llmHealthURL       = "http://localhost:5000/health"
	useBatchProcessing = true
	batchSize          = 5

	testingMode = false
	testLimit   = 10
)

var (
	categories          = make(map[string]bool)
	escapeRgx           = regexp.MustCompile(`\\u([0-9a-fA-F]{4})`)
	httpClient          = &http.Client{Timeout: 30000000 * time.Second}
	containerPatterns   = regexp.MustCompile(`(?i)(vpc|vnet|subnet|network|cluster|namespace|resource.?group)`)
	llmServiceAvailable = false

	popularServices = map[string]bool{
		"ec2": true, "s3": true, "lambda": true, "rds": true, "dynamodb": true,
		"vpc": true, "eks": true, "ecs": true, "kubernetes": true, "docker": true,
	}
)

func Generate() error {
	log.Println("🚀 Enhanced Icon Generator - JSON Output Only")
	if testingMode {
		log.Printf("🧪 TESTING MODE: %d icons per category", testLimit)
	}

	if useLLMEnrichment {
		if checkLLMService() {
			log.Println("✅ LLM service connected")
			llmServiceAvailable = true
		} else {
			log.Println("⚠️  LLM service unavailable - using fallback")
			llmServiceAvailable = false
		}
	}

	if err := os.MkdirAll(outputDir, 0750); err != nil {
		log.Fatalf("Failed to create output directory: %v", err)
	}

	pendingIcons := make([]PendingIcon, 0)
	categoryCount := make(map[string]int)

	c := colly.NewCollector()
	c.OnError(func(r *colly.Response, err error) {
		log.Fatalf("Scraping error: %v", err)
	})

	c.OnHTML("div", func(e *colly.HTMLElement) {
		if e.Attr("class") == "icon" {
			unescaped := getUnescaped(e.Attr("onclick"))
			link := strings.TrimSuffix(strings.TrimPrefix(unescaped, "clickIcon(\""), "\")")

			if link != "" && strings.Contains(link, "%") {
				parts := strings.Split(link, "%")
				if len(parts) > 0 {
					category := strings.ToUpper(parts[0])

					if testingMode && categoryCount[category] >= testLimit {
						return
					}

					categories[category] = true
					categoryCount[category]++
					title := e.Attr("data-search")

					pendingIcons = append(pendingIcons, PendingIcon{
						Category:    category,
						Title:       title,
						Link:        link,
						DisplayName: cleanDisplayName(title),
					})
				}
			}
		}
	})

	_ = c.Visit(sourceURL)

	log.Printf("✅ Collected %d icons from %d categories", len(pendingIcons), len(categories))

	allIcons := make([]*IconPayload, 0)
	providerIcons := make(map[string][]*IconPayload)
	timestamp := time.Now().UTC().Format(time.RFC3339)

	if useLLMEnrichment && llmServiceAvailable && useBatchProcessing {
		log.Printf("⚡ Batch processing %d icons...", len(pendingIcons))

		for i := 0; i < len(pendingIcons); i += batchSize {
			end := i + batchSize
			if end > len(pendingIcons) {
				end = len(pendingIcons)
			}

			batch := pendingIcons[i:end]
			enrichments := batchEnrichIcons(batch)

			for j, pending := range batch {
				var enrichment LLMEnrichmentResponse
				if j < len(enrichments) {
					enrichment = enrichments[j]
				}

				icon := createIconPayload(pending.Category, pending.Title, pending.Link, pending.DisplayName, enrichment, timestamp)
				allIcons = append(allIcons, icon)
				providerIcons[icon.Provider] = append(providerIcons[icon.Provider], icon)
			}

			log.Printf("   Processed batch %d-%d of %d", i+1, end, len(pendingIcons))
		}
	} else {
		log.Printf("🔄 Processing %d icons individually...", len(pendingIcons))
		for _, pending := range pendingIcons {
			var enrichment LLMEnrichmentResponse
			if useLLMEnrichment && llmServiceAvailable {
				enrichment = getLLMEnrichment(pending.Category, pending.Title, pending.DisplayName)
			}

			icon := createIconPayload(pending.Category, pending.Title, pending.Link, pending.DisplayName, enrichment, timestamp)
			allIcons = append(allIcons, icon)
			providerIcons[icon.Provider] = append(providerIcons[icon.Provider], icon)
		}
	}

	log.Printf("✅ Enrichment complete: %d icons processed", len(allIcons))

	for category := range categories {
		path := filepath.Join(outputDir, strings.ToLower(category))
		os.MkdirAll(path, 0750)
	}

	for provider, icons := range providerIcons {
		providerKey := getProviderKey(provider)
		path := filepath.Join(outputDir, providerKey, fmt.Sprintf("%s.json", providerKey))
		if err := writeJSON(path, icons); err != nil {
			log.Fatalf("Failed to write %s: %v", path, err)
		}
		log.Printf("📝 %s: %d icons", provider, len(icons))
	}

	ragPath := filepath.Join(outputDir, jsonFile)
	if err := writeJSON(ragPath, allIcons); err != nil {
		log.Fatalf("Failed to write RAG JSON: %v", err)
	}
	log.Printf("🎯 RAG-optimized JSON: %s (%d icons)", ragPath, len(allIcons))

	log.Println("✅ Generation complete!")
	return nil
}

func checkLLMService() bool {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, "GET", llmHealthURL, nil)
	if err != nil {
		return false
	}

	resp, err := httpClient.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()

	return resp.StatusCode == http.StatusOK
}

func batchEnrichIcons(pending []PendingIcon) []LLMEnrichmentResponse {
	batchInput := BatchClassifyRequest{
		Icons: make([]BatchIconInput, len(pending)),
	}

	for i, p := range pending {
		batchInput.Icons[i] = BatchIconInput{
			Provider:    p.Category,
			Title:       p.Title,
			DisplayName: p.DisplayName,
		}
	}

	jsonData, err := json.Marshal(batchInput)
	if err != nil {
		return make([]LLMEnrichmentResponse, len(pending))
	}

	ctx, cancel := context.WithTimeout(context.Background(), 36000000*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, "POST", llmBatchURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return make([]LLMEnrichmentResponse, len(pending))
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := httpClient.Do(req)
	if err != nil {
		return make([]LLMEnrichmentResponse, len(pending))
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return make([]LLMEnrichmentResponse, len(pending))
	}

	var batchResp BatchClassifyResponse
	if err := json.NewDecoder(resp.Body).Decode(&batchResp); err != nil {
		return make([]LLMEnrichmentResponse, len(pending))
	}

	return batchResp.Results
}

func createIconPayload(provider, title, link, displayName string, enrichment LLMEnrichmentResponse, timestamp string) *IconPayload {
	slug := generateSlug(provider, title)
	iconifyID := verifyIconifyID(provider, title, slug)

	description := fmt.Sprintf("%s from %s. %s", displayName, provider, enrichment.TechnicalIntent)
	iconPosition := "center"
	if enrichment.IsContainer {
		iconPosition = "top-left"
	}

	return &IconPayload{
		ID:              uuid.New().String(),
		Slug:            slug,
		IconifyID:       iconifyID,
		Provider:        getFullProviderName(provider),
		URL:             fmt.Sprintf("%s/%s", sourceURL, link),
		SemanticProfile: enrichment.SemanticProfile,
		DisplayName:     displayName,
		Aliases:         arrayToJSON(enrichment.Aliases),
		Description:     description,
		TechnicalIntent: enrichment.TechnicalIntent,
		ShapeType:       enrichment.ShapeType,
		DefaultWidth:    determineDefaultWidth(enrichment.Category),
		IsContainer:     enrichment.IsContainer,
		IconPosition:    iconPosition,
		ColorTheme:      enrichment.BrandColor,
		Popularity:      calculatePopularity(title),
		Tags:            arrayToJSON(enrichment.Tags),
		LastScraped:     timestamp,
	}
}

func getLLMEnrichment(provider, title, displayName string) LLMEnrichmentResponse {
	payload := map[string]string{
		"provider":     provider,
		"title":        title,
		"display_name": displayName,
	}

	jsonData, _ := json.Marshal(payload)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	req, _ := http.NewRequestWithContext(ctx, "POST", llmServiceURL, bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")

	resp, err := httpClient.Do(req)
	if err != nil {
		return LLMEnrichmentResponse{}
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return LLMEnrichmentResponse{}
	}

	var enrichment LLMEnrichmentResponse
	if err := json.NewDecoder(resp.Body).Decode(&enrichment); err != nil {
		return LLMEnrichmentResponse{}
	}

	return enrichment
}

func verifyIconifyID(provider, title, slug string) string {
	queries := []string{
		fmt.Sprintf("%s %s", provider, title),
		title,
		slug,
	}

	for _, query := range queries {
		url := fmt.Sprintf("https://api.iconify.design/search?query=%s&limit=3", query)
		resp, err := httpClient.Get(url)
		if err != nil {
			continue
		}

		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()

		var result IconifySearchResult
		if err := json.Unmarshal(body, &result); err != nil {
			continue
		}

		if result.Total > 0 && len(result.Icons) > 0 {
			return result.Icons[0]
		}
	}

	providerLower := strings.ToLower(provider)
	titleClean := regexp.MustCompile(`[^a-z0-9-]`).ReplaceAllString(
		strings.ToLower(strings.ReplaceAll(title, " ", "-")), "")
	return fmt.Sprintf("logos:%s-%s", providerLower, titleClean)
}

func generateSlug(provider, title string) string {
	clean := regexp.MustCompile(`[^a-z0-9-]`).ReplaceAllString(
		strings.ToLower(strings.ReplaceAll(title, " ", "-")), "")
	return fmt.Sprintf("%s-%s", strings.ToLower(provider), clean)
}

func cleanDisplayName(title string) string {
	name := strings.TrimSpace(title)
	name = strings.ReplaceAll(strings.ReplaceAll(name, "_", " "), "-", " ")
	words := strings.Fields(name)
	for i, word := range words {
		if len(word) > 0 {
			words[i] = strings.ToUpper(string(word[0])) + strings.ToLower(word[1:])
		}
	}
	return strings.Join(words, " ")
}

func determineShapeType(category string) string {
	return "image"
}

func determineDefaultWidth(category string) int {
	switch category {
	case "network", "container":
		return 128
	case "storage", "database":
		return 96
	default:
		return 64
	}
}

func calculatePopularity(title string) float32 {
	titleLower := strings.ToLower(title)
	for service := range popularServices {
		if strings.Contains(titleLower, service) {
			return 1.0
		}
	}
	return 0.5
}

func arrayToJSON(arr []string) string {
	if len(arr) == 0 {
		return "[]"
	}
	data, _ := json.Marshal(arr)
	return string(data)
}

func getFullProviderName(provider string) string {
	providerMap := map[string]string{
		"AWS": "Amazon Web Services", "AZURE": "Microsoft Azure",
		"GCP": "Google Cloud Platform", "ESSENTIALS": "Essential Icons",
		"DEV": "Development Tools", "INFRA": "Infrastructure",
		"TECH": "Technology", "SOCIAL": "Social Media", "EMOTIONS": "Emojis",
	}
	if fullName, exists := providerMap[strings.ToUpper(provider)]; exists {
		return fullName
	}
	return strings.Title(strings.ToLower(provider))
}

func getProviderKey(fullProviderName string) string {
	reverseMap := map[string]string{
		"Amazon Web Services": "aws", "Microsoft Azure": "azure",
		"Google Cloud Platform": "gcp", "Essential Icons": "essentials",
		"Development Tools": "dev", "Infrastructure": "infra",
		"Technology": "tech", "Social Media": "social", "Emojis": "emotions",
	}
	if key, exists := reverseMap[fullProviderName]; exists {
		return key
	}
	return strings.ToLower(fullProviderName)
}

func getUnescaped(escaped string) string {
	return escapeRgx.ReplaceAllStringFunc(escaped, func(match string) string {
		hexCode := match[2:]
		unicodeValue, _ := strconv.ParseInt(hexCode, 16, 32)
		return string(rune(unicodeValue))
	})
}

func writeJSON(path string, data interface{}) error {
	f, err := os.OpenFile(filepath.Clean(path), os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0600)
	if err != nil {
		return fmt.Errorf("error opening file %s: %w", path, err)
	}
	defer f.Close()

	e := json.NewEncoder(f)
	e.SetEscapeHTML(false)
	e.SetIndent("", "  ")
	return e.Encode(data)
}