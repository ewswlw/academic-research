# AI Dev Tasks Process Instructions

## Overview

This document provides a comprehensive, step-by-step guide for implementing the AI Dev Tasks workflow in your development process. This structured approach ensures systematic feature development from ideation to implementation with built-in checkpoints for verification.

## Core Workflow: 5-Step Process

### Step 1: Create Product Requirements Document (PRD)

**Purpose**: Define the blueprint for your feature with clear requirements and scope.

**Process**:
1. **Initiate PRD Creation**:
   ```
   Use @create-prd.md
   Here's the feature I want to build: [Describe your feature in detail]
   Reference these files to help you: [Optional: @file1.py @file2.ts]
   ```

2. **Clarifying Questions Phase**:
   - The AI will ask specific questions to gather sufficient detail
   - Questions will cover: problem/goal, target users, core functionality, user stories, acceptance criteria, scope boundaries, data requirements, design considerations, and edge cases
   - Provide clear, detailed answers to ensure comprehensive PRD

3. **PRD Generation**:
   - AI creates a structured PRD with sections: Introduction/Overview, Goals, User Stories, Functional Requirements, Non-Goals, Design Considerations, Technical Considerations, Success Metrics, and Open Questions
   - PRD is saved as `prd-[feature-name].md` in `/tasks/` directory
   - Target audience is junior developers - requirements are explicit and unambiguous

**Best Practices**:
- Be specific about the problem you're solving
- Provide user stories in format: "As a [user type], I want to [action] so that [benefit]"
- Clearly define what's in scope and what's not
- Include measurable success criteria

### Step 2: Generate Task List from PRD

**Purpose**: Break down the PRD into actionable, step-by-step implementation tasks.

**Process**:
1. **Initiate Task Generation**:
   ```
   Now take @prd-[feature-name].md and create tasks using @generate-tasks.md
   ```

2. **Phase 1 - Parent Tasks**:
   - AI analyzes the PRD and existing codebase
   - Generates high-level parent tasks (typically 5-7 tasks)
   - Presents parent tasks without sub-tasks
   - Waits for user confirmation with "Go"

3. **Phase 2 - Sub-Tasks**:
   - After user confirms, AI breaks down each parent task into detailed sub-tasks
   - Sub-tasks are actionable and implementation-focused
   - Considers existing codebase patterns and architecture

4. **File Identification**:
   - AI identifies all relevant files that need creation or modification
   - Includes corresponding test files
   - Lists files with brief descriptions of their purpose

**Output Structure**:
```markdown
## Relevant Files
- `path/to/file1.ts` - Description of purpose
- `path/to/file1.test.ts` - Unit tests for file1.ts

## Tasks
- [ ] 1.0 Parent Task Title
  - [ ] 1.1 Sub-task description
  - [ ] 1.2 Sub-task description
- [ ] 2.0 Parent Task Title
  - [ ] 2.1 Sub-task description
```

### Step 3: Begin Task Implementation

**Purpose**: Start systematic implementation with user approval at each step.

**Process**:
1. **Start with First Task**:
   ```
   Please start on task 1.1 and use @process-task-list.md
   ```

2. **Implementation Protocol**:
   - Work on ONE sub-task at a time
   - After completing a sub-task, mark it as `[x]`
   - Pause and wait for user approval before proceeding
   - User responds with "yes" or "y" to continue

3. **Parent Task Completion**:
   - When all sub-tasks under a parent task are complete:
     - Run full test suite (`pytest`, `npm test`, etc.)
     - Stage changes (`git add .`)
     - Clean up temporary files
     - Commit with descriptive message using conventional commit format

**Commit Message Format**:
```
git commit -m "feat: add payment validation logic" -m "- Validates card type and expiry" -m "- Adds unit tests for edge cases" -m "Related to T123 in PRD"
```

### Step 4: Review and Approve

**Purpose**: Ensure quality and alignment with requirements at each step.

**Process**:
1. **Review Changes**: After each sub-task completion, review the implemented changes
2. **Approve or Request Changes**:
   - If satisfied: Respond with "yes" or "y"
   - If changes needed: Provide specific feedback for corrections
3. **Track Progress**: Watch the task list update with completed items marked `[x]`

### Step 5: Complete and Verify

**Purpose**: Ensure the entire feature is properly implemented and tested.

**Process**:
1. **Final Testing**: Run comprehensive test suite
2. **Code Review**: Review all implemented changes
3. **Documentation**: Update relevant documentation
4. **Deployment**: Deploy or prepare for deployment

## File Management

### Directory Structure
```
/tasks/
├── prd-[feature-name].md          # Product Requirements Document
├── tasks-prd-[feature-name].md    # Generated task list
└── [other project files]
```

### File Naming Conventions
- PRD files: `prd-[feature-name].md`
- Task files: `tasks-prd-[feature-name].md`
- Use kebab-case for feature names

## Quality Assurance

### Before Starting Implementation
1. **Analyze entire codebase** to understand existing patterns
2. **Map file dependencies** and relationships
3. **Identify all affected files** before making changes
4. **Consider performance implications** of changes
5. **Plan proper error handling** strategies
6. **Consider testing requirements** for each component

### During Implementation
1. **Follow existing code patterns** and conventions
2. **Write tests alongside code** implementation
3. **Use descriptive variable and function names**
4. **Keep functions small and focused**
5. **Implement proper error messages**
6. **Use consistent naming conventions**

### After Implementation
1. **Run all tests** to ensure no regressions
2. **Update documentation** as needed
3. **Review for security implications**
4. **Check for performance impacts**
5. **Verify user experience** meets requirements

## Troubleshooting

### Common Issues and Solutions

**Issue**: AI generates overly complex or incorrect code
**Solution**: Break down tasks into smaller, more specific sub-tasks

**Issue**: AI gets lost or confused during implementation
**Solution**: Provide more context in the initial PRD and clarify requirements

**Issue**: Tests fail after implementation
**Solution**: Write tests first (TDD approach) or ensure tests are updated with implementation

**Issue**: Code doesn't follow existing patterns
**Solution**: Provide more context about existing codebase structure and conventions

### When to Pause and Reassess
1. **Multiple failed attempts** at a single sub-task
2. **Significant deviation** from original requirements
3. **Performance or security concerns** arise
4. **Scope creep** beyond original PRD
5. **Technical debt** accumulation

## Advanced Techniques

### For Complex Features
1. **Break into multiple PRDs** for very large features
2. **Create separate task lists** for different components
3. **Use feature branches** for parallel development
4. **Implement incrementally** with user feedback at each stage

### For Team Collaboration
1. **Share PRDs** with stakeholders for review
2. **Use task lists** as communication tools
3. **Track progress** through task completion
4. **Document decisions** and rationale

### For Different Project Types
1. **Web Applications**: Focus on UI/UX requirements and API design
2. **Backend Services**: Emphasize API contracts and data models
3. **Libraries**: Prioritize API design and documentation
4. **CLI Tools**: Focus on user experience and error handling

## Success Metrics

### Process Metrics
- **PRD Quality**: Completeness and clarity of requirements
- **Task Breakdown**: Appropriate granularity of sub-tasks
- **Implementation Speed**: Time to complete each sub-task
- **Error Rate**: Number of corrections needed per task

### Code Quality Metrics
- **Test Coverage**: Percentage of code covered by tests
- **Code Complexity**: Cyclomatic complexity of functions
- **Documentation**: Completeness of inline and external docs
- **Performance**: Impact on application performance

## Continuous Improvement

### Regular Reviews
1. **Process Effectiveness**: How well did the workflow work?
2. **AI Performance**: How accurate were the AI's implementations?
3. **User Experience**: How smooth was the development process?
4. **Code Quality**: How maintainable is the resulting code?

### Iterative Refinement
1. **Update PRD templates** based on project needs
2. **Refine task generation** for better breakdown
3. **Improve implementation guidance** for common patterns
4. **Enhance quality checks** and validation steps

## Conclusion

This structured approach transforms AI-assisted development from a black box into a systematic, controllable process. By following these steps, you can:

- **Maintain control** over the development process
- **Ensure quality** through regular checkpoints
- **Track progress** with clear visual indicators
- **Debug issues** more effectively with granular tasks
- **Build confidence** in AI-generated code through systematic review

Remember: The goal is not perfection, but systematic improvement. Each iteration should make the process more effective and the resulting code more reliable. 