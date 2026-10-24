# Can I use Java + Vulkan for the training, or do I explicitly have to use PyTorch and similar
topic 741791 | by **Xelvant** (https://www.kaggle.com/xelvant) | posted 2026-09-17 | votes 0 | comments 2 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741791

I had a question regarding the competition's submission environment

I am considering to use Java and Vulkan using LWJGL's bindings as the backend for the compute and training, rather than CUDA/PyTorch directly, as I want to participate using a programming language I am best suited around

Would a competition submission be allowed to:

- Install/use a JDK available in the notebook environment, or otherwise execute a Java application from the notebook?

- Load LWJGL's native libraries?

- Initialize the NVIDIA Vulkan driver and create a Vulkan compute device/queue?

- Use the assigned competition GPU through Vulkan for arbitrary compute workloads?

- Include the required native Vulkan/LWJGL binaries with the submission if they are redistributable and compatible with the competition's licensing requirements?

I would still use the Kaggle Notebook as the submission entry point and produce the required "submission.csv", the actual tensor/ML computation would be performed by my Java/Vulkan backend.

Is this technically supported in the competition's GPU submission environment, or are GPU submissions restricted to the CUDA/Python ecosystem?

I'm mainly trying to determine whether Vulkan GPU compute is viable before building the model around it. Thanks!

## Comments (1 top-level)

- **inversion** **[Kaggle]** (2026-09-19, votes 1)
  The short answer is, I don't know that anyone's done it. It might be possible? But you'd have to experiment.
    - **Xelvant** (2026-09-19, votes 0)
      Fair enough, thanks for the clarification. I already have a Java + Vulkan backend ready, and I wanted to test on how well it performs in a real benchmark
